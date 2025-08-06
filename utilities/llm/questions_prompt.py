from langchain_core.prompts import PromptTemplate

# Base prompt template
base_prompt = """
As a senior teacher, your task is to create {questionPrompt} 
The question should be based on the topic '{topicTitle}' for a class of grade '{classGrade}'. Ensure that the question is at a '{difficultyLevel}' difficulty level.

Follow these guidelines:
1. Use this context to formulate the question. 
<context> 
{context} 
</context>

2. Incorporate the following additional information: '{additionalInfo}'.
3. Ensure age-appropriate language for {classGrade} and {difficultyLevel} difficulty level. 
4. Make distractors plausible but clearly incorrect
5. Strictly follow this JSON schema:
{schema}
6. Return only the JSON object. No explanations.
7. Do not add any hint for answer in the questions.


"""

# New base prompt template for messages
message_prompt = """  
Update the question based on the user query.  
user query: {user_query}
- Follow this JSON schema: {schema}  
- Return only the JSON object, no explanations.  
- No hints for the answer.  
- If the request is irrelevant, remind the user that you only update questions.  
"""  


# Schemas for different question types
schemas = {
    "multiple_choice": """{
      "question_text": "String",
      "choices": ["Array<String>"],
      "answer": "choiceIndex"
    }""",
    "true_false": """{
      "question_text": "String",
      "answer": "'0'|'1'"
    }""",
    "open_response": """{
      "question_text": "String",
      "suggested_answer": "String"
    }""",
     "check_all": """{
        "question_text": "String",
        "choices": ["Array<String>"],
        "answer": ["Array<choiceIndex>"]
    }""",
    "numeric": """{
      "question_text": "String",
      "answer": "Number"
    }""",
    "fill_in_the_blank": """{
      "question_text": "String with atleast 2 '_____' placeholders",
          "choices": [
            ["first blank's Option 1", "first blank's Option 2", "first blank's Option 3"],
            ["second blank's Option 1", "second blank's Option 2", "second blank's Option 3"]
          ],
          "answer": ["Correct answer from first blank Options ", "Correct answer from second blank's Option"]
    }""",
    "matching": """{
        "question_text": "String",
        "pairs": "Array<{"left": "String", "right": "String"}>"
        "answer": "Array<{"left": "String", "right": "String"}>"
    }""",
     "grouping": """{
        "question_text": "String",
        "groups": "Array<{"name": String, "terms": Array<String>}>"
        "answer": "Array<{"name": String, "terms": Array<String>}>"
    }""",
    "sorting": """{
        "question_text": "String",
        "terms": "Array<String>",
        "answer": "Array<String>"
    }"""
}

# Question prompts for different types
question_prompts = {
    "multiple_choice": """Create a multiple-choice question with four choices, where only one choice is correct.""",
    "true_false": """Create a true/false question with a clear and definitive answer.""",
    "open_response": """Create an open response question with a suggested answer for guidance.""",
    "check_all": """Create a 'Check All' multiple-choice question with four choices, where multiple answers can be correct. """,
    "numeric": """Create a 'Numeric' question based on the given topic. The question should involve basic arithmetic operations 
    like addition, subtraction, multiplication, or division, and must have a single numeric answer.""",
    "fill_in_the_blank": """Create a fill-in-the-blanks question with:
- At least 2 contextual blanks marked with '_____'
- 3 plausible options per blank
- Answers must be exact matches from given options.""",
    "matching": """
Create a 'Matching' question with at least 2 pairs based on the given topic. Ensure each pair is logically connected and relevant to the topic, forming a meaningful matching exercise. Return the response in JSON format with the following structure:

- **question_text**: A string containing the question.
- **pairs**: It holds an array of pairs where right is not related to left.
- **answer**: An array containing the correct pairs i.e. right is related to left.
"""
,
    "grouping": """Create a 'Grouping' question with 2 groups and up to 4 terms based on the given topic. Each group should have a name and a list of terms relevant to the topic.""",
    "sorting": """Create a 'Sorting' question based on the given topic. The question should include a list of terms 
that the student needs to arrange in the correct order. Ensure the terms are logically related to the topic 
and require a specific sequence, making the activity both challenging and educational."""



}

# Function to generate the prompt
def generate_question_prompt(question_type, topic_title, class_grade, difficulty_level, additional_info, context=""):
    """
    Generates a formatted question prompt based on the requested question type.
    
    Parameters:
        question_type (str): The type of question (e.g., "multiple_choice", "true_false", "open_response").
        topic_title (str): The topic title.
        class_grade (str): The grade level of the class.
        difficulty_level (str): The difficulty level of the question.
        additional_info (str): Any additional information for the question.
        context (str): Context to use for formulating the question.
        
    Returns:
        str: A formatted prompt.
    """
    # Validate question type
    if question_type not in schemas or question_type not in question_prompts:
        raise ValueError(f"Invalid question type '{question_type}'. Valid types are: {list(schemas.keys())}")

    # Create a PromptTemplate and fill in the values
    prompt_template = PromptTemplate.from_template(base_prompt).partial(
        questionPrompt=question_prompts[question_type],
        schema=schemas[question_type]
    )
    
    # Format with user inputs
    formatted_prompt = prompt_template.partial(
        topicTitle=topic_title,
        classGrade=class_grade,
        difficultyLevel=difficulty_level,
        additionalInfo=additional_info
        # context=context
    )
    # print("formatted_prompt",formatted_prompt)   
    return formatted_prompt

# Function to generate the message prompt
def generate_message_prompt(user_query, schema, context=""):
    """
    Generates a formatted message prompt based on the user's query.
    
    Parameters:
        user_query (str): The user's query.
        schema (str): The JSON schema for the question.
        context (str): Context to use for formulating the question.
        
    Returns:
        str: A formatted prompt.
    """
    # Create a PromptTemplate and fill in the values
    prompt_template = PromptTemplate.from_template(message_prompt).partial(
        schema=schema
    )
    
    # Format with user inputs
    formatted_prompt = prompt_template.partial(
        user_query=user_query,
        context=context
    )
    
    return formatted_prompt

# # Example usage
# try:
#     question_type = "multiple_choice"  # Options: "multiple_choice", "true_false", "open_response"
#     prompt = generate_question_prompt(
#         question_type=question_type,
#         topic_title="Newton's Laws of Motion",
#         class_grade="8",
#         difficulty_level="Medium",
#         additional_info="Focus on the second law of motion and its applications.",
#         context="provided examples in physics"
#     )
#     print(prompt)
# except ValueError as e:
#     print(e)

# Example usage
# try:
#     user_query = "Explain the process of photosynthesis."
#     schema = schemas["open_response"]  # Use the schema for open response questions
#     prompt = generate_message_prompt(
#         user_query=user_query,
#         schema=schema,
#         context="provided examples in biology"
#     )
#     print(prompt)
# except ValueError as e:
#     print(e)
