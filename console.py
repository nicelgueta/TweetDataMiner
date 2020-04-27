from mongo import DB
from config import V,C
from setup import check_y_n, update_core_attributes

def menu():
    print('\n--------\nMining Bot Console\n--------')
    print('-'*20)
    print('Main Menu - key the number of the action you want to take')
    print('1. View/change keywords to stream')
    print('2. Update DB configs from latest config.py file (will overwrite filters)')
    print('3. View/change tweet filters')
    print('4. Start/Stop Bot')
    print('5. Download saved collection of tweets to local machine')
    print('6. Close console')
    print('-'*20)

def options():
    choice = str(input('Select an option number: '))
    if not choice in ['1','2','3','4','5','6']:
        print('Wrong choice try again')
        options()
    #choices
    if choice == '1':
        choice_1()
    elif choice == '2':
        choice_2()
    elif choice == '3':
        choice_3()
    elif choice == '4':
        choice_4()
    elif choice == '5':
        choice_5()
    elif choice == '6':
        quit()
    else:
        pass
    #end
    main()

def choice_1():
    print('Current keywords: %s\n'%str(DB.getkv('tweetKeywords')))
    if check_y_n('Change keywords? (y/n)'):
        new_list = input('Enter new keywords separated by spaces: ')
        new_list = new_list.split()
        DB.updatekv('tweetKeywords',new_list)
        print('New keywords updated')

def choice_2():
    print('-'*20)
    print('Current configs in local file:\n')
    for key in V:
        print('%s:%s'%(key,V[key]))
    print('-'*20)
    print('Current configs on cloud DB:\n')
    for key in V:
        print('%s:%s'%(key,DB.getkv(key)))
    if check_y_n('\nUpdate configs from file? (y/n) '):
        update_core_attributes(DB,C,V,overwrite=True)
        print('DB configs updated\n')
    else:
        print('Operation cancelled\n')

def choice_3():
    filters = DB.getkv('tweetFiltersDict')
    print('-'*20)
    print('Current filters:\n')
    for filter in filters:
        print('%s: %s'%(filter,filters[filter]))
    if check_y_n('\nDo you want to change/reset a filter? (y/n)'):
        field = input('\nEnter name of field to change/reset: ')
        new_dict = {}
        new_dict['operator'] = input('Choose filter operator (gt,lt,eq..) or just type "-r" to reset to None: ')
        if not new_dict['operator'] == '-r':
            new_dict['value'] = input('Choose filter value: ')
            try:
                new_dict['value'] = eval(new_dict['value'])
            except NameError: #is a native string
                pass
            filters[field] = new_dict
        else:
            filters[field] = {'value':None,'operator':'gt'}
        DB.updatekv('tweetFiltersDict',filters)
        print('\nNew filters updated\n')

def choice_4():
    print('Current Bot settings:\n---------------')
    print('--> Keywords to search: %s'%str(DB.getkv('tweetKeywords')))
    print('--> Collection to store tweets: %s'%str(DB.getkv('collectionToStoreTweets')))
    print('--> Tweet fields to be saved: %s\n'%str(DB.getkv('permittedTweetColumns')))
    print('--> Filters to be applied:')
    filter_dict = DB.getkv('tweetFiltersDict')
    filter_dict = {field:filter_dict[field] for field in filter_dict if (filter_dict[field] == 0 or filter_dict[field]['value'])}
    for filter in filter_dict:
        print('----->%s %s %s'%(filter,filter_dict[filter]['operator'],filter_dict[filter]['value']) )
    print('-'*20)
    stream = DB.getkv('streamLive')
    status = 'RUNNING' if stream else 'OFF'
    action = 'turn off the bot' if stream else 'activate the Bot'
    print('Bot is currently %s'%status)
    if check_y_n('\nAre you sure you want to %s? (y/n) '%action):
        DB.updatekv('streamLive',not stream)
        print('Action completed')

def choice_5():
    collection = input('Enter name of mongo DB collection to download: ')
    path = input('Enter path to save downloaded tweets: ')
    df = DB.load_collection_as_table(collection=collection,as_df=True)
    df.to_csv(path+collection+'.csv')
    print('\n\n%s saved to %s!'%(collection,path))
def main():
    menu()
    options()

main()
