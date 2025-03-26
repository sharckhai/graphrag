# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine tuning prompts for Community Reports Rating."""

GENERATE_REPORT_RATING_PROMPT = """

You are a helpful agent tasked with rating the importance of a given text in the context of the provided domain and persona. Your goal is to provide a rating that reflects the relevance and significance of the text to the specified domain and persona. Use your expertise to evaluate the text based on the importance criteria and assign a float score between 0-10. Only respond with the text description of the importance criteria. Use the provided example data format to guide your response. Ignore the content of the example data and focus on the structure.

######################
-Examples-
######################

### Example 1

# Domain

Microservices Architecture in Backend Development

# Persona

You are an expert in analyzing complex codebases with a focus on microservices architecture. You are skilled at identifying service boundaries, understanding inter-service communication, and discovering how different components interact in distributed systems. You are adept at helping teams optimize service orchestration, improve reliability, and ensure maintainability in large-scale backend applications.

# Data


Service: PaymentService
Methods:
  - processPayment(amount: double, userId: string): PaymentResult
  - refundPayment(transactionId: string, reason: string): RefundResult

Dependencies:
  - AuthService for user authentication
  - OrderService for order validation

Recent commits indicate that PaymentService now broadcasts payment status events via an internal messaging queue to NotificationService and ReportService. The updated processPayment method publishes a "PAYMENT_COMPLETED" message containing the userId, amount, and timestamp.


# Importance Criteria

A float score between 0-10 that represents the relevance of the snippet to identifying critical system components, understanding service dependencies, and evaluating the overall microservices architecture. A score of 1 would mean the data is trivial or irrelevant to distributed system design, whereas a score of 10 would mean it is highly significant for pinpointing architectural patterns or potential improvements.#############################

### Example 2

# Domain

Frontend Development with React

# Persona

You are a senior frontend developer specializing in React-based applications. You are skilled at analyzing component structures, state management patterns, and user interface performance. You excel at identifying best practices in reusable React components, guiding large teams to build efficient and maintainable user interfaces, and optimizing for both readability and scalability of code.

# Data

Component: UserProfileCard.jsx

import React from 'react';
import UserAvatar from './UserAvatar';
import UserDetails from './UserDetails';

function UserProfileCard({{ user }}) {{
  return (
    <div className="user-profile-card">
      <UserAvatar avatarUrl={{user.avatarUrl}} />
      <UserDetails name={{user.name}} email={{user.email}} />
    </div>
  );
}}

export default UserProfileCard;


# Importance Criteria

A float score between 0-10 that represents the relevance of the snippet to identifying critical system components, understanding service dependencies, and evaluating the overall microservices architecture. A score of 1 would mean the data is trivial or irrelevant to distributed system design, whereas a score of 10 would mean it is highly significant for pinpointing architectural patterns or potential improvements.#############################

### Example 3

# Domain

Data Structures and Algorithm Design

# Persona

You are an expert in algorithm engineering with a focus on optimizing data structures and graph-based problem-solving. You specialize in identifying patterns for efficient lookups, minimizing time complexity, and discovering relationships among large sets of connected nodes. You excel at helping developers refine their algorithms to be both scalable and robust.

# Data


Snippet from GraphUtils.java:

public class GraphUtils {{

    public static boolean isCyclicDirected(Map<String, List<String>> adjacencyList) {{
        Set<String> visited = new HashSet<>();
        Set<String> recStack = new HashSet<>();

        for (String node : adjacencyList.keySet()) {{
            if (detectCycle(node, adjacencyList, visited, recStack)) {{
                return true;
            }}
        }}
        return false;
    }}

    private static boolean detectCycle(String node, Map<String, List<String>> adjacencyList,
                                       Set<String> visited, Set<String> recStack) {{
        if (!visited.contains(node)) {{
            visited.add(node);
            recStack.add(node);

            for (String neighbor : adjacencyList.getOrDefault(node, Collections.emptyList())) {{
                if (!visited.contains(neighbor) && detectCycle(neighbor, adjacencyList, visited, recStack)) {{
                    return true;
                }} else if (recStack.contains(neighbor)) {{
                    return true;
                }}
            }}
        }}
        recStack.remove(node);
        return false;
    }}
}}

# Importance Criteria

A float score between 0-10 that represents the relevance of the snippet to identifying critical system components, understanding service dependencies, and evaluating the overall microservices architecture. A score of 1 would mean the data is trivial or irrelevant to distributed system design, whereas a score of 10 would mean it is highly significant for pinpointing architectural patterns or potential improvements.#############################


#############################
-Real Data-
#############################

# Domain

{domain}

# Persona

{persona}

Now provide an importance criteria for the following data, given the domain and persona:

# Data

{input_text}

# Importance Criteria


"""
