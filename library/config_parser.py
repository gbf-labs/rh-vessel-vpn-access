# CONFIG PARSER
def configSectionParser(config,section):
    
    # INITIALIZE
    dict1 = {}
    options = config.options(section)
    
    # LOOP CONFIG
    for option in options:

        try:
        
            # SET RETURN
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    
    # RETURN
    return dict1