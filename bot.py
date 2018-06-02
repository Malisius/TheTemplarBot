#This code made available under GNU GPLv3. See LICENSE for more info.

import telebot
from telebot import types
from InstagramAPI.InstagramAPI import InstagramAPI
from time import sleep
import traceback
from threading import Thread

telegram_token = "513408030:AAEiNbStV2Equ1QeGF8T7C7HqA17iulEIvY"
insta_user = 'peteroertel'
insta_password ='$mlxn5w1'

bot = telebot.TeleBot(telegram_token)
#Set up out dictionary with which we'll track our interactions with different users
interactions = {}

#Handle all incoming text messages
#I'll do all the logic myself
@bot.message_handler(func=lambda m: True)
def catch_all(message):
    thread = Thread(target=handle_message, args=(message, ))
    thread.start()

def handle_message(message):
    try:
        #If this message isn't text, ignore it completely
        if(not isinstance(message.text, str)):
            return False
            
        #For any incoming group messages, direct the user to the DMs
        if message.chat.type == "group":
            bot.reply_to(message, "Hello! Start a conversation with me personally to get started!")
            
        #The rest of the real logic can go here
        else:    
            #pull out the sending user's id, for easy access
            sender = message.from_user.id
            
            #make an empty interaction for this user if we don't already have one
            #Apparently python breaks horribly if I don't do this here
            if sender not in interactions:
                interactions[sender] = {'waitingonusername':False, 'waitingonpassword':False, 'waitingoncount':False, 'waitingonchoice1':False, 'waitingonchoice2':False, 'waitingonplatform':False, 'waiting':False}
                
            #If this user has been put on hold, tell them to sod off and ignore this message
            if interactions[sender]['waiting']:
                bot.send_message(message.chat.id, "Working, please wait before sending another message.")
                return False
                
            #Incoming start command
            if "/start" in message.text:
                #Get started by prompting for an instagram username
                interactions[sender]['waitingonusername'] = True
                bot.reply_to(message, "Welcome! Let's get started! This bot needs your username to perform its analysis. Reply with your Instagram username to begin! (Don't include the '@' symbol)")
                print("New interaction with " + str(sender))
            #Okay, now that we've got an interaction going, we can start checking for user input
            #First, let's get the user's insta username down
            #We'll check to see if the username is valid immediately, and if it's not,
            #we'll reply with an error and return out so they can try again
            elif(interactions[sender]['waitingonusername']):
                #Put the user on hold
                interactions[sender]['waiting'] = True
                
                bot.send_message(message.chat.id, "Okay, let me try to find your username.")
                interactions[sender]['instauser'] = message.text
                interactions[sender]['api'] = InstagramAPI(insta_user, insta_password)

                #Make sure our login was successful before moving on
                if(interactions[sender]['api'].login()):
                    #Before we can do anything else, we need to see if this user's account exists, and is public
                    #If not, we'll prompt them to fix it and delete the whole interaction
                    if(interactions[sender]['api'].searchUsername(message.text)):
                        interactions[sender]['user'] = interactions[sender]['api'].LastJson['user']
                        #If this account is private, bounce out
                        if(interactions[sender]['user']['is_private']):
                            bot.send_message(message.chat.id, "This account is private. Sorry, but I can only analyze an account that's set to public.")
                            return False
                    else:
                        bot.reply_to(message, "Couldn't find that username. Check the spelling and try again.")
                        return False
                        
                    #okay, we've got a valid username to check now, so let's get the info on what the user wants
                    interactions[sender]['waitingonusername'] = False
                    interactions[sender]['loggedin'] = True
                    markup = types.ReplyKeyboardMarkup()
                    itembtn1 = types.KeyboardButton('50')
                    itembtn2 = types.KeyboardButton('100')
                    itembtn3 = types.KeyboardButton('200')
                    itembtn4 = types.KeyboardButton('400')
                    markup.row(itembtn1, itembtn2, itembtn3, itembtn4)
                    bot.send_message(message.chat.id, "How many of your most recent followers would you like to check?", reply_markup=markup)
                    bot.send_message(message.chat.id, "You can select an option below, or type any integer.")
                    #bot.send_message(message.chat.id, "Careful though; selecting ALL might return a Fatal Error. Use with caution.")
                    interactions[sender]['waitingoncount'] = True
                    
                    #Take the user off hold
                    interactions[sender]['waiting'] = False
                #If we failed to login, let the user know how to contact us. This is not an easily solved problem
                else:
                    bot.reply_to(message, "Failed to log in. Contact @peteroertel on Instagram.")
                    interactions[sender]['waitingonusername'] = True
            #We've got a count, now we just need to see what about their followers they want to check
            elif(interactions[sender]['waitingoncount']):
                try:
                    if(message.text == "All"):
                        interactions[sender]['count'] = 0
                    else:
                        interactions[sender]['count'] = int(message.text)
                    #If the user chose more than 1k, bring it down to 1k
                    if interactions[sender]['count'] > 1000:
                        interactions[sender]['count'] = 1000
                    
                    #Put the user on hold
                    interactions[sender]['waiting'] = True
                        
                    interactions[sender]['waitingoncount'] = False
                    markup = types.ReplyKeyboardMarkup()
                    itembtn1 = types.KeyboardButton('1.')
                    itembtn2 = types.KeyboardButton('2.')
                    itembtn3 = types.KeyboardButton('3.')
                    markup.row(itembtn1, itembtn2, itembtn3)
                    bot.send_message(message.chat.id, "Now which accounts would you like to see?", reply_markup=markup)
                    bot.send_message(message.chat.id, "1. Accounts that follow me and have no posts.")
                    bot.send_message(message.chat.id, "2. Accounts that follow me and more than 1000 people.")
                    bot.send_message(message.chat.id, "3. Accounts that follow me, 1000+ people, and who have fewer than 10 posts.")
                    interactions[sender]['waitingonchoice1'] = True
                    #Take the user off hold
                    interactions[sender]['waiting'] = False
                except ValueError:
                    bot.reply_to(message, "Not a valid number, please select one of the options below.")
            #Okay, choice incoming. Here's where all the magic really happens
            elif(interactions[sender]['waitingonchoice1']):
                #Before we do anything, make sure the user actually made a valid choice
                if ("1." not in message.text) and ("2." not in message.text) and ("3." not in message.text):
                    bot.send_message(message.chat.id, "Please select one of the buttons below.")
                    return False
                else:
                    #Put the user on hold
                    interactions[sender]['waiting'] = True
                    
                    #Pretty sure the choice is valid, so save it and propmpt for the next one
                    interactions[sender]['choice1'] = message.text
                    markup = types.ReplyKeyboardMarkup()
                    itembtn1 = types.KeyboardButton('1.')
                    itembtn2 = types.KeyboardButton('2.')
                    itembtn3 = types.KeyboardButton('3.')
                    itembtn4 = types.KeyboardButton('4.')
                    markup.row(itembtn1, itembtn2, itembtn3,itembtn4)
                    bot.send_message(message.chat.id, "Of these accounts, show the ones that haven't: ")
                    bot.send_message(message.chat.id, "1. Liked any of my 6 most recent posts.")
                    bot.send_message(message.chat.id, "2. Commented on any of my 6 most recent posts.")
                    bot.send_message(message.chat.id, "3. Neither liked nor commented on my 6 most recent posts.")
                    bot.send_message(message.chat.id, "4. Skip this step", reply_markup=markup)
                    interactions[sender]['waitingonchoice1'] = False
                    interactions[sender]['waitingonchoice2'] = True
                    #Take the user off hold
                    interactions[sender]['waiting'] = False
            elif(interactions[sender]['waitingonchoice2']):
                #Check for a valid choice real quick
                if ("1." not in message.text) and ("2." not in message.text) and ("3." not in message.text) and ("4." not in message.text):
                    bot.send_message(message.chat.id, "Please select one of the buttons below.")
                    return False
                else:
                    interactions[sender]['choice2'] = message.text
                    
                #Put the user on hold
                interactions[sender]['waiting'] = True    
                
                #Let the user know we're working
                bot.send_message(message.chat.id, "Okay, give me just a minute to work.")
                
                #No matter what they choose, we'll need to call down their followers
                followers = interactions[sender]['api'].getTotalFollowers(interactions[sender]['user']['pk'], limit=interactions[sender]['count'])
                
                interactions[sender]['followers'] = {}
                #Immediately pull out all the usernames into a list
                #Also set a counter to break if we go over the user's selected count
                count = 0
                for i in followers:
                    interactions[sender]['followers'][i['pk']] = i['username']
                    print("Adding to list: " + i['username'])
                    count = count + 1
                    if count >= interactions[sender]['count'] and interactions[sender]['count'] != 0:
                        break
                        
                #For debugging, print out the number of followers we have saved
                print("Total followers: " + str(len(interactions[sender]['followers'])))
                
                #Let the user know how many followers we found
                bot.send_message(message.chat.id, "Okay, checking " + str(len(interactions[sender]['followers'])) + " followers.")
                
                #We'll also need all of our user's recent posts
                #We can skip this if they chose option 4 in part 2 though
                if("4." in interactions[sender]['choice2']):
                    print("Skipping gathering this user's media.")
                else:
                    interactions[sender]['api'].getUserFeed(interactions[sender]['user']['pk'])
                    media = interactions[sender]['api'].LastJson
                    interactions[sender]['mediaids'] = []
                    #Just get the 10 most recent though
                    count = 0
                    for i in media['items']:
                        interactions[sender]['mediaids'].append(i['id'])
                        count  = count + 1
                        if count >= 6:
                            break
                
                #Making a quick user dict, so we can store the json of each user
                user = {}
                #Start a counter so we can give updates to our user on how we're doing
                count = 0
                total = len(interactions[sender]['followers'])
                checkbreak = 10
                if total <= 200:
                    checkbreak = 5
                #populate the dict before we start filtering
                #We're doing this now so we don't have to make tons of api calls later more than once
                for i in interactions[sender]['followers']:
                    #If we're at an increment of 50, let the user know
                    if count % (total//checkbreak) == 0:
                        print("Checked " + str(count) + "/" + str(len(interactions[sender]['followers'])))
                        bot.send_message(message.chat.id, "Collected " + str(count) + " out of " + str(len(interactions[sender]['followers'])) + " followers.")
                    count += 1
                    
                    #We'll set the collected user state for this iteration to failed real quick, so the code
                    #will enter this loop and continue trying to collect it until it succeeds
                    user[i] = {'status':'fail'}
                    while user[i]['status'] == 'fail':
                        if(interactions[sender]['api'].searchUsername(interactions[sender]['followers'][i])):
                            print("Found data for: " + interactions[sender]['followers'][i])
                            user[i] = interactions[sender]['api'].LastJson['user']
                            user[i]['status'] = 'ok'
                        else:
                            print("Couldn't find data for: " + interactions[sender]['followers'][i])
                            print("Relogging the api real quick...")
                            interactions[sender]['api'].login(force=True)
                            print("Sleeping for 10sec, trying to make sure the login worked.")
                            sleep(10)
                
                #Let the user know we've started performing our analysis
                bot.send_message(message.chat.id, "Finished collecting data, performing analysis.")
                
                #FIRST OPTION STUFF
                #If they made the first or third choice, we need to do the few posts filter
                if ("1." in interactions[sender]['choice1']) or ("3." in interactions[sender]['choice1']):
                    #Prep a list to store the keys that we'll delete later
                    to_delete = []
                    for i in interactions[sender]['followers']:
                        #Pull down the current user's media count
                        feedcount = user[i]['media_count']
                        #We need to change our flag count depending on which option the user picked
                        if("1." in interactions[sender]['choice1']):
                            flagcount = 0
                        else:
                            flagcount = 9
                        if feedcount > flagcount:
                            print("Removing for too many posts: " + interactions[sender]['followers'][i])
                            to_delete.append(i)
                            #Also delete from our dict of jsons, just so we don't accidentally try to iterate through a missing key later
                            del user[i]
                        else:
                            print(interactions[sender]['followers'][i] + " has few enough posts. They stay on the list.")
                
                    #Now that we've got the keys to delete stored, go ahead and get it done
                    for i in to_delete:
                        del interactions[sender]['followers'][i]
                        
                #Now let's check accounts that are following more than 1000 people
                if("2." in interactions[sender]['choice1'] or "3." in interactions[sender]['choice1']):
                    to_delete = []
                    for i in interactions[sender]['followers']:
                        if user[i]['following_count']:
                            to_delete.append(i)
                            print("Removing for to few following: " + interactions[sender]['followers'][i])
                    #Do the actual deletions
                    for i in to_delete:
                        del interactions[sender]['followers'][i]
                     
                
                    
                    
                #SECOND OPTION STUFF
                #We can skip this whole damn section if they chose 4 in the second options
                if "4." not in interactions[sender]['choice2']:
                    failcount = 0
                    for i in interactions[sender]['mediaids']:
                        #ONLY DO THIS STEP if the user selected option 1 or 3 in the second choice
                        #This is where we're removing people who've liked any of our recent posts
                        if((("1." in interactions[sender]['choice2']) or ("3." in interactions[sender]['choice2'])) and (interactions[sender]['api'].getMediaLikers(i))):
                            #Get the usernames out
                            likers = interactions[sender]['api'].LastJson['users']
                            #Step through each username
                            for k in likers:
                                #If the username comes up in our list of followers, remove it from such list
                                #The idea here is any usernames left in the followers list when we're done
                                #   will be the ones with no comments or likes
                                if k['pk'] in interactions[sender]['followers']:
                                    print("Removing for likes: " + interactions[sender]['followers'][k['pk']])
                                    del interactions[sender]['followers'][k['pk']]
                        #ONLY DO THIS STEP if the user selected options 2 or 3
                        #This is where we're removing people who've commented on any of our recent posts
                        if((("2." in interactions[sender]['choice2']) or ("3." in interactions[sender]['choice2'])) and interactions[sender]['api'].getMediaComments(i)):
                            comments = interactions[sender]['api'].LastJson['comments']
                            for k in comments:
                                if k['user']['pk'] in interactions[sender]['followers']:
                                    print("Removing for comments: " + interactions[sender]['followers'][k['user']['pk']])
                                    del interactions[sender]['followers'][k['user']['pk']] 
                else:
                    print("Skipping all the media checks since the user picked 4 in part 2")
                
                
                     
                #Now that we're done with additional filtering, send out our findings
                #For debugging, print out the number of remaining followers first off
                print("Found potentials: " + str(len(interactions[sender]['followers'])))
                
                if len(interactions[sender]['followers']) == 0:
                    bot.send_message(message.chat.id, "Huh, I actually didn't find any accounts matching the criteria.")
                    bot.send_message(message.chat.id, "If you'd like to perform another check, just reply with /start again!")
                else:
                    #Set up the string we'll send directly to the user later
                    send_string = ""
                    count = 1
                   
                    for i in interactions[sender]['followers']:
                        #If we're already at 20 people, send it and start over
                        if count % 20 == 0:
                            bot.send_message(message.chat.id, send_string, parse_mode='HTML', disable_web_page_preview=True)
                            send_string = ""
                        send_string = send_string + str(count) + ". " + "<a href='https://instagram.com/_u/" + interactions[sender]['followers'][i] + "'>@" + interactions[sender]['followers'][i] + "</a>\n"
                        count += 1
                    bot.send_message(message.chat.id, send_string, parse_mode='HTML', disable_web_page_preview=True)    
                    bot.send_message(message.chat.id, "If you'd like to perform another check, just reply with /start again!")
                    
                #Take the user off hold
                interactions[sender]['waiting'] = False
                    
            #Big-ass catch-all, just in case we're sent garbage when we weren't expecting it
            else:
                bot.send_message(message.chat.id, "Hello! Reply with /start to get started!")
            
        #Dump message to console, for extra debugging points
        print(message.text)
    except:
        traceback.print_exc()
        print("FATAL ERROR: BAD BAD BAD")
        print("<<Check to make sure the API isn't maxed out whydontya>>")
        bot.send_message(message.chat.id, "FATAL ERROR: API maxed out.")
        bot.send_message(message.chat.id, "Try again with fewer followers, or with a different analysis option.")
    
while True:
    try:
        print("Starting Telegram Bot...")
        bot.polling()
    except:
        traceback.print_exc()
        print("FATAL ERROR: Telegram bot failed, restarting.")
        sleep(3)
