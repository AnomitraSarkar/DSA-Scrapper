import requests

LEETCODE_URL = "https://leetcode.com/graphql"
USERNAME = "AnomitraSarkar"

query = '''
query userProblemsSolved($username: String!) {
    allQuestionsCount {    
        difficulty    
        count  
        }
        matchedUser(username: $username ) {
            problemsSolvedBeatsStats { 
                difficulty
                percentage    
                }
        submitStatsGlobal {
            acSubmissionNum {        
                difficulty        
                count      
                    }    
                }  
            }             
        }

'''

print(query)
vars = {"username" : USERNAME}
resp = requests.post(LEETCODE_URL, json={"query":query, "variables": vars})
data = resp.json()

print(data['data']['matchedUser']['submitStatsGlobal'])