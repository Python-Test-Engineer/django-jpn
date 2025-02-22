import os
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console

console = Console()

# Load environment variables in a file called .env
# Print the key prefixes to help with any debugging

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key:
    print(f"OpenAI API Key exists and begins:{openai_api_key[:14]}...")
else:
    print("OpenAI API Key not set")

client = OpenAI()
MODEL = "gpt-4o-mini"


class Agent:
    def __init__(self, client: client, system: str = "") -> None:
        self.client = client
        self.system = system
        self.messages: list = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        """Sets the message and executes the agent"""
        if message:
            self.messages.append({"role": "user", "content": message})
            result = self.execute()
            self.messages.append({"role": "assistant", "content": result})
            return result
        else:
            print("NO MESSAGE")

    def execute(self):
        """Executes the ageLLM request and returns the result"""
        completion = client.chat.completions.create(model=MODEL, messages=self.messages)
        return completion.choices[0].message.content


system_prompt = """
You run in a loop of THOUGHT, ACTION, OBSERVATION.

You have two tools available for your ACTIONS - calculate_total and get_product_price so that you can get the total price of an item requested by the user.

# 1. calculate_total:

if amount = 200
then calculate_total(amount)
return amount * 1.2

Runs the calculate_total function and returns a JSON FORMAT output as follows:
{"result": 240, "fn": "calculate_total", "next": "PAUSE"}

# 2. get_product_price:

This uses the get_product_price function and passes in the value of the product
e.g. get_product_price('bike')

This uses the get_product_price with a product = 'bike', finds the price of the bike and then returns a JSON FORMAT output as follows:
{"result": 200, "fn": "get_product_price", "next": "PAUSE"}

Here is an example session:

User Question: What is total cost of a bike including VAT?

AI Response: THOUGHT: I need to find the cost of a bike|ACTION|get_product_price|bike

You will be called again with the result of get_product_price as the OBSERVATION and will have OBSERVATION|200 sent as another LLM query along with previous messages.

Then the next message will be:

THOUGHT: I need to calculate the total including the VAT|ACTION|calculate_total|200

The result wil be passed as another query as OBSERVATION|240 along with previous messages.

If you have the ANSWER, output it as the ANSWER in this format:

ANSWER|The price of the bike including VAT is 240

"""


def calculate_total(amount):
    amount = int(amount)
    return int(amount * 1.2)


def get_product_price(product):
    if product == "bike":
        return 100
    if product == "tv":
        return 200
    if product == "laptop":
        return 300
    return None


# We now loop over the query until an answer is found or the'max_iterations' is reached
answers = []


def loop(max_iterations=10, query: str = ""):
    agent = Agent(client=client, system=system_prompt)
    tools = ["calculate_total", "get_product_price"]
    next_prompt = query
    console.print("[dark_orange]\nSTARTING LOOP...\n[/]")
    i = 0
    while i < max_iterations:
        i += 1
        # This is the AI bit
        # -------------------------
        result = agent(next_prompt)
        # -------------------------
        # Here we loop over ACTIONS getting OBSERVATIONS and continue until we get an ANSWER
        if "ACTION" in result:
            # extract function and arguments
            next = result.split("|")
            print(next)
            next_function = next[2].strip()
            next_arg = str(next[3]).strip()
            # if a tool/function exists - run it and prepend with OBSERVATION as we descrbed in system prompt
            if next_function in tools:
                result_tool = eval(f"{next_function}('{next_arg}')")
                # OBSERVATIONS passed back into next_prompt
                next_prompt = f"OBSERVATION: {result_tool}"
                console.print(f"[green]{next_prompt}[/]")
                print("------------------------------\n")
            else:
                next_prompt = "OBSERVATION: Tool not found"
            continue
        # if we have a final ANSWER, store it and break out of loop
        if "ANSWER" in result:
            # the result at top has final result
            print("======================================")
            console.print(f"[cyan bold]Answer found:\n\t{result}\n[/]")
            print("======================================")
            answers.append(result)
            break  # we have an answer so break out of loop


loop(query="What is cost of a bike including VAT?")

# loop(query="What is cost of a tv including VAT?")
# loop(query="What is cost of a laptop including VAT?")
# print("\n=========== SUMMARY ANSWERS ===========")
# for answer in answers:
#     print(answer)
