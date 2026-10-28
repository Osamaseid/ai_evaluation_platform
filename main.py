
def calculate_average(numbers):
    return sum(numbers) / len(numbers)


def agent(user_message):
    message = user_message.lower()

    if "hello" in message:
        return "Hello! I am your Python assistant."

    elif "average" in message:
        numbers = [70, 80, 90]
        result = calculate_average(numbers)
        return f"The average is {result}."

    elif "python" in message:
        return "Python is a programming language."

    else:
        return "I don't know that yet. Try another question."


while True:
    question = input("You: ")

    if question.lower() == "exit":
        print("Agent: Goodbye!")
        break

    answer = agent(question)
    print("Agent:", answer)
