import actions

#will need to read in user input
#then maps this to a corrisponding function and passes the args to th efunction
#executes the functions
#and then loops back

def startREPL(scope):
    while True:
        try:
            print("> ", end = "")
            #read
            textInput = input().split() 
            cmd= textInput[0]
            args = textInput[1:]

            if cmd == "q" or cmd == "quit":
                print("Exiting...")
                break

            #lookup and check argc
            action = actions.actionMap[cmd]

            if action.argc != len(args):
                print(cmd, " requires arg length of ", action.argc)
                continue

            #execute
            action.func(scope, args)
        except Exception as e:
            # maybe reset state here
            print("an exception occured:", e)
