# TalkToYourDeadRelatives
Talk to your deceased family and friends!

Edit this value to choose the method type for prompting GPT-3

```METHOD = 0 #0: Task description / 1: Prompt for info on user / 2: Recent messages```

Edit this value to choose the GPT model

```MODEL = 1 #0: ada (worst model) / 1: davinci (best model)```

Edit this value to change the the minimum amount of words that a conversation that is used to prompt the model will have

```MIN_WORDS_IN_SELECTED_CONVO = 50```

Edit this value to change the number of messages pulled from the database

```MAX_MESSAGES = 10000```

Edit this value to change the max number of tokens in GPT-3's response

```MAX_TOKEN_RESPONSE = 40```

This value is a constant and should not be changed by the user. 

```MAX_CHARACTERS_TOTAL = 2048*4```

This value is the user's private key for OpenAI (it should start with "sk-")

```PRIVATE_KEY = ""```
