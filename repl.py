import actions

#will need to read in user input
#then maps this to a corrisponding function and passes the args to th efunction
#executes the functions
#and then loops back

def startREPL(scope):
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
        action = actions.actionMap.get(cmd, actions.errorAction) #provide default fallback if cmd not found

        if action.argc != len(args):
            print(cmd, " requires arg length of ", action.argc)
            continue

        #execute
        action.func(scope, args)
                    
