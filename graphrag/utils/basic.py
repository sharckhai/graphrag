import tiktoken

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count the number of tokens in a text string.
    
    Parameters
    ----------
    text : str
        The text to count tokens for
    encoding_name : str, optional
        The name of the encoding to use, by default "cl100k_base"
        
    Returns
    -------
    int
        The number of tokens in the text
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return len(tokens)