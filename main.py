def calculate_avrage(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def agent(user_message):
    message = user_massage.lower()

    if "hello" in massage:
        return "Hello, how can i assist you today?"
    elif "avrage" in message:
        numbers = [int(num) for num in message.split() if num.isdigit()]
        average = calculate_avrage(numbers)
        return f"The avrage of the provided numbers is: {average}"

    elif "python" in message:
        return "Python is a versatile programming language that is great for web development, data analysis, artificial intelligence, and more."
    else:
        return "I'm sorry, I didn't understand that. Can you please rephrase your question or request?"
while True:
    question = input("You:")

    if question.lower() == "exit":
        print("Goodbye!")
        break

    answer = agent(question)
    print("Agent:", answer)
