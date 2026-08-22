#will need to read in user input
#then maps this to a corrisponding function and passes the args to th efunction
#executes the functions
#and then loops back

class Action :
    def __init__(self, argc, func):
        self.argc = argc
        self.func = func

#requires argc = 1
def testFunc(args):
    print("test: ", args[0])

def errorFunc(args):
    print ("cmd not found")

#stores all possible actions and there corrisponding cmd string
actionMap = {
    "test": Action(1, testFunc),

    #Add all commands here, e.g. changing scale or print ML description
    "auto": Action(0, None),
}

#unique error action that is the default value for the map
errorAction=Action(0, errorFunc)

while True:
    print("> ")
    #read
    textInput = input().split() 
    cmd= textInput[0]
    args = textInput[1:]

    if cmd == "q" or cmd == "quit":
        print("Exiting...")
        break

    #lookup and check argc
    action = actionMap.get(cmd, errorAction) #provide default fallback if cmd not found


    if action.argc != len(args):
        print(cmd, " requires arg length of ", action.argc)
        continue

    #execute
    action.func(args)
                

