from os.path import expanduser
import sqlite3
import openai
import math
from textblob import TextBlob as tb

METHOD = 0 #0: Task description / 1: Prompt for info on user / 2: Recent messages
MODEL = 1 #0: ada (worst model) / 1: davinci (best model)

MIN_WORDS_IN_SELECTED_CONVO = 50
MAX_MESSAGES = 1000
MAX_TOKEN_RESPONSE = 40
MAX_CHARACTERS_TOTAL = 2048*4
PRIVATE_KEY = ""

def main():
    m = METHOD 
    phone_raw = input("Choose a phone number: ")
    phone = "+1"+phone_raw
    continue_last_input = input("Continue last conversation? (Y/N): ")
    continue_last = continue_last_input.lower()!="n"
    messages = get_messages(phone)
    convos = split_into_conversations(messages)
    most_recent = convos[-1] if continue_last else None
    sorted_documents = sort_conversations(convos)
    prompt = get_gpt_prompt(convos,sorted_documents,method=m)
    #print("\n-----\n".join([get_text_repn(c[0],with_labels=True)[:20] for c in sorted_documents[:5]]))
    responses = interact_with_gpt(prompt,phone,most_recent)
    print(compare_sentiment(messages,responses))
    
    print_for_evaluation(responses,m)

def compare_sentiment(messages,responses):
    message = tb(" ".join([x[0] for x in messages if x[1]==0]))
    response = tb(" ".join([x[0] for x in responses if x[1]==0]))
    return abs(response.sentiment.polarity-message.sentiment.polarity)
    
def get_gpt_prompt(convos,sorted_documents,method):
    prompt = ""
    if method==0:
        prompt+="The following are text conversations between User1 and User2. Continue the conversation in the style User2. Do not start a new conversation.\nNew conversation:\n"
        for i in range(len(sorted_documents)):
            temp = prompt+get_text_repn(sorted_documents[i][0],with_labels=True)
            if len(temp)>5500:
                break
            else:
                prompt = temp+"\nNew conversation:\n"
    elif method==1:
        print("Please fill in the following sentences about User2.")
        relationship = input("User2 is my ")
        job = input("User2 works as a ")
        description = input("User2 is a ")
        likes = input("User2 likes ")
        prompt += "User2 is User1's "+relationship+". User2 works as a "+job+". User2 is a " +description+". User2 likes "+likes+".\nNew conversation:\n"
        for i in range(len(sorted_documents)):
            temp = prompt+get_text_repn(sorted_documents[i][0],with_labels=True)
            if len(temp)>5500:
                break
            else:
                prompt = temp+"\nNew conversation:\n"

    else:
        for i in reversed(list(range(len(convos)))):
            temp = get_text_repn(convos[i],with_labels=True)+"\nNew conversation:\n"+prompt
            if len(temp)>5500:
                break
            else:
                prompt = temp

    return prompt[:5500] 

def sort_conversations(convos):
    document_list = [c for c in convos if len(get_text_repn(c,with_labels=False).split(" "))>=MIN_WORDS_IN_SELECTED_CONVO]
    bloblist = [tb(get_text_repn(c,with_labels=False)) for c in document_list]
    document_scores = [None]*len(bloblist)
    for i, doc in enumerate(document_list):
        blob = bloblist[i]
        scores = {word: tfidf(word, blob, bloblist) for word in blob.words}
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        document_scores[i] = (doc, sum([x[1] for x in sorted_words[:3]]))
    return  sorted(document_scores,key=lambda x: x[1],reverse=True)

def get_messages(phone):
    conn = sqlite3.connect(expanduser("~")+'/Library/Messages/chat.db')
    c = conn.cursor()
    c.execute('''select ROWID from handle where id=:id and service='iMessage';''',{"id":phone})
    handle_id = c.fetchone()[0]
    c.execute('''select text,is_from_me,date from (select date,text,is_from_me from message where handle_id=:handle_id and type=0 and associated_message_type=0 order by date desc limit :max_msg) order by date asc;''',{"handle_id":handle_id,'max_msg':MAX_MESSAGES})
    messages = c.fetchall()
    conn.close()
    return [x for x in messages if x[0] is not None and "http" not in x[0]]

def get_text_repn(conversation, with_labels):
    if not with_labels:
        return "\n".join([x[0] for x in conversation])
    else:
        return "\n".join(["User1: "+x[0] if x[1] else "User2: "+x[0] for x in conversation])

def make_nice(phone):
    return "("+phone[2:5]+") "+phone[5:8]+"-"+phone[8:]

def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob.words)

def tfidf(word, blob, bloblist):
    return (blob.words.count(word) / len(blob.words)) * (math.log(len(bloblist) / (1 + n_containing(word, bloblist))))

def split_into_conversations(messages):
    messages = [(x[0],x[1],int(str(x[2])[:-9])) for x in messages]
    conversations = []
    conversation = [(messages[0][0],messages[0][1])]
    prev = messages[0][2]
    for message in messages[1:]:
        if message[2]-prev>=3600*3:
            conversations.append(conversation)
            conversation = [(message[0],message[1])]
        else:
            conversation.append((message[0],message[1]))
        prev = message[2]
    conversations.append(conversation)
    return conversations

def print_for_evaluation(responses,m):
    print("\n\nResult (method = "+str(m)+"):\n ")
    print(get_text_repn(responses,with_labels=True))
    return 


def interact_with_gpt(prompt,phone,last_convo):
    openai.api_key = PRIVATE_KEY
    print("\rSIMULATED MESSAGES WITH "+make_nice(phone))
    if last_convo:
        prompt+=get_text_repn(last_convo,with_labels=True)
        print(get_text_repn(last_convo[-5:],with_labels=True))

    new_coversation = []
    prompt = prompt.strip()
    print(prompt)
    new = input("Type a message, leave blank to continue, or 'quit' to leave): ")    
    while new.lower() != "quit" and len(prompt)<MAX_CHARACTERS_TOTAL:
        if len(new)>0:
            prompt+="\nUser1: "+new+'\nUser2:'
            new_coversation.append((new,1))
        response = openai.Completion.create(engine="davinci" if MODEL else "ada", prompt=prompt, max_tokens=MAX_TOKEN_RESPONSE)
        response_text = dict(response)['choices'][0]['text'].strip().split("User1:")[0].strip()
        prompt+=response_text
        new_coversation.append((response_text,0))
        print('User2: '+response_text)
        new = input("User1: ")

    return new_coversation




if __name__ == "__main__":
    main()


