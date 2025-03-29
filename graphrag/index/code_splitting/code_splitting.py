import ast
from typing import List, Tuple
import numpy as np  # Add this import at the top

from graphrag.index.text_splitting.text_splitting import Tokenizer
from graphrag.index.text_splitting.text_splitting import TextChunk
from graphrag.index.text_splitting.text_splitting import ProgressTicker


class ScopeTracker(ast.NodeVisitor):
    """
    A DFS-based AST visitor that tracks, for each line, the list of (type, name)
    of the class/function scopes that line belongs to.
    """
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.n_lines = len(source_lines)
        # line_scopes[i] will hold a list of (type, name), e.g. [("class","MyClass"), ("function","foo")]
        self.line_scopes = [[] for _ in range(self.n_lines)]
        # We'll keep a stack of (type, name) as we traverse the AST
        self.scope_stack: List[Tuple[str, str]] = []

    def _add_scope_to_lines(self, start_line: int, end_line: int, scope: Tuple[str, str]):
        """Add a single scope to line range."""
        start_idx = start_line - 1  # Convert to 0-based
        end_idx = min(end_line, self.n_lines)
        for i in range(start_idx, end_idx):
            if scope not in self.line_scopes[i]:  # Prevent duplicates
                self.line_scopes[i].append(scope)

    def visit_ClassDef(self, node: ast.ClassDef):
        scope = ("class", node.name)
        self.scope_stack.append(scope)
        # Add this class's scope to all its lines
        self._add_scope_to_lines(node.lineno, node.end_lineno, scope)
        # Visit children (which might be nested functions/classes)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        scope = ("function", node.name)
        self.scope_stack.append(scope)
        # Add this function's scope to all its lines
        self._add_scope_to_lines(node.lineno, node.end_lineno, scope)
        # Visit children (which might be nested functions)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        scope = ("async_function", node.name)
        self.scope_stack.append(scope)
        self._add_scope_to_lines(node.lineno, node.end_lineno, scope)
        self.generic_visit(node)
        self.scope_stack.pop()


class ImportCollector(ast.NodeVisitor):
    """Collects all import statements from a Python file."""
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.imports: List[str] = []
        
    def visit_Import(self, node: ast.Import):
        # Get the exact line from source
        line = self.source_lines[node.lineno - 1]
        self.imports.append(line)
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        # For multi-line imports, we need to collect all lines from start to end
        start_line = node.lineno - 1  # Convert to 0-based index
        end_line = getattr(node, 'end_lineno', start_line)
        if end_line is None:
            end_line = start_line
        
        # Collect all lines of the import statement
        import_lines = self.source_lines[start_line:end_line]
        complete_import = '\n'.join(import_lines)
        self.imports.append(complete_import)


def build_scope_string(scopes: list[tuple[str, str]]) -> str:
    """
    Convert a list of (scope_type, scope_name), e.g.
      [("class","class1"), ("function","func1"), ("function","func2")]
    into a multiline Python-like definition snippet:
    
    class class1:
        def func1():
            def func2():
    """
    lines = []
    for i, (scope_type, scope_name) in enumerate(scopes):
        indent = "    " * i  # 4 spaces per nesting level
        if scope_type == "class":
            lines.append(f"{indent}class {scope_name}:")
        elif scope_type == "function":
            lines.append(f"{indent}def {scope_name}():")
        elif scope_type == "async_function":
            lines.append(f"{indent}async def {scope_name}():")

    return "\n".join(lines)


def chunk_code_with_ast_scope(
    code: str,
    tokenizer,
    max_tokens: int,
    token_overlap: int = 0
):
    """
    1. Parse the code into an AST.
    2. Collect all imports.
    3. For each line in the file, we know which class/function scopes it's in.
    4. Chunk from top to bottom until we reach max_tokens, only breaking on line boundaries.
    5. For each chunk, prepend imports and scope metadata.
    """
    source_lines = code.split('\n')
    tree = ast.parse(code)
    
    # Collect imports
    import_collector = ImportCollector(source_lines)
    import_collector.visit(tree)
    import_header = '\n'.join(import_collector.imports)
    
    # Get scope information
    tracker = ScopeTracker(source_lines)
    tracker.visit(tree)
    line_scopes = tracker.line_scopes
    
    # Debug: Print scopes for each line
    #for i, scopes in enumerate(line_scopes):
    #    if scopes:  # Only print lines that have scopes
    #        print(f"Line {i+1}: {scopes}")
    
    n_lines = len(source_lines)
    chunks = []
    start_idx = 0
    
    while start_idx < n_lines:
        chunk_lines = []
        idx = start_idx
        first_line_scope = line_scopes[idx] if idx < n_lines else []
        
        # Calculate tokens for imports and scope header
        scope_header = build_scope_string(first_line_scope)
        headers = []
        if chunks:  # Only add headers if this is not the first chunk
            if import_header:
                headers.append(import_header)
            if scope_header:
                headers.append(scope_header)
        header = '\n'.join(headers)
        current_tokens = len(tokenizer.encode(header)) if headers else 0
        
        while idx < n_lines:
            line = source_lines[idx]
            # Count tokens for the line plus newline
            test_chunk = '\n'.join(chunk_lines + [line])
            if headers:  # Only add headers if we have them (not first chunk)
                test_chunk = header + '\n' + test_chunk
            
            chunk_tokens = len(tokenizer.encode(test_chunk))
            
            # If this would exceed our limit and we have lines, break
            if chunk_tokens > max_tokens and chunk_lines:
                break
                
            # Otherwise add the line
            chunk_lines.append(line)
            current_tokens = chunk_tokens
            idx += 1
            
            # If we're at the token limit, break even if we could add more lines
            if current_tokens >= max_tokens:
                break
        
        # Create the chunk with imports and scope header
        chunk_parts = []
        if chunks:  # Only add headers if this is not the first chunk
            if import_header:
                chunk_parts.append(import_header)
            if scope_header:
                chunk_parts.append(scope_header)
        chunk_parts.append('\n'.join(chunk_lines))
        chunk_text = '\n'.join(chunk_parts)
            
        chunks.append(chunk_text)
        
        if idx >= n_lines:
            break
            
        # Calculate how many lines we need to overlap to meet the token_overlap requirement
        if token_overlap > 0:
            try:
                # Try batch encoding if supported by tokenizer
                line_token_lengths = np.array([len(tokens) for tokens in tokenizer.encode(chunk_lines)])
            except (AttributeError, TypeError):
                # Fallback to individual encoding if batch encoding not supported
                line_token_lengths = np.array([len(tokenizer.encode(line)) for line in chunk_lines])
                
            # Reverse the array and get cumulative sum
            cumulative_tokens = np.cumsum(line_token_lengths[::-1])
            # Find where cumulative sum exceeds token_overlap
            overlap_mask = cumulative_tokens <= token_overlap
            overlap_lines = np.sum(overlap_mask)
            
            # Calculate new start index with overlap
            new_start = idx - overlap_lines
        else:
            new_start = idx
            
        start_idx = max(new_start, start_idx + 1)  # Ensure we always advance
    
    return chunks


def split_multiple_code_texts_on_tokens(
    texts: list[str],
    tokenizer: Tokenizer,
    tick: ProgressTicker,
) -> list[TextChunk]:
    """Split multiple code texts and return chunks with metadata using the tokenizer.
    Respects line boundaries when splitting."""
    result = []
    
    for source_doc_idx, text in enumerate(texts):
        chunks = chunk_code_with_ast_scope(
            text, 
            tokenizer, 
            tokenizer.tokens_per_chunk,
            tokenizer.chunk_overlap
        )
        for chunk in chunks:
            result.append(TextChunk(
                text_chunk=chunk,
                source_doc_indices=[source_doc_idx],
                n_tokens=len(tokenizer.encode(chunk))
            ))
        if tick:
            tick(1)
            
    return result