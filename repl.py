import actions

#will need to read in user input
#then maps this to a corrisponding function and passes the args to th efunction
#executes the functions
#and then loops back

def startREPL(scope):
    print("o-see-lloscope REPL, type a command and press enter to execute an action.")
    print("(type 'help' for action manual)")

    while True:
        try:
            print("> ")
            #read
            textInput = input().split() 
            cmd= textInput[0]
            args = textInput[1:]

            if cmd == "q" or cmd == "quit":
                print("exiting...")
                break

            #lookup and check argc
            action = actions.actionMap.get(cmd, actions.errorAction) #provide default fallback if cmd not found

            if action.argc != len(args):
                print(cmd, " requires arg length of ", action.argc)
                # TODO: print usage here as well
                continue

            #execute
            action.func(scope, args)
        except Exception as e:
            # maybe reset state here
            print("an exception occured:", e)
