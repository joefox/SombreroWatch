'use strict';
const MLBStatsAPI = require('mlb-stats-api');
const AWS = require('aws-sdk')


const DB_SECRET_ARN = `arn:aws:secretsmanager:us-east-1:648249859534:secret:rds-db-credentials/cluster-KKUA46G2OPELRAV6SWDUUQIAIE/postgres-EXGFEZ`;
const DB_RESOURCE_ARN = `arn:aws:rds:us-east-1:648249859534:cluster:sombrero-db`;
const APPLICATION_CONSUMER_SECRET = process.env.TWITTER_APP_SECRET;
const ACCESS_TOKEN_SECRET = process.env.TWITTER_BOT_SECRET;
const APPLICATION_CONSUMER_KEY = `9NAlHgia69p4d9VEury1f8Doi`
const ACCESS_TOKEN = `2440847334-L8fjnsMue6NRp7YVo5SHLPp1uLb04ee3BQDStfk`
const DB_NAME = process.env.DB_NAME;

const Twit = require('twit');

module.exports.tweet = async event => {
const T = new Twit({
  consumer_key: APPLICATION_CONSUMER_KEY,
  consumer_secret: APPLICATION_CONSUMER_SECRET,
  access_token: ACCESS_TOKEN,
  access_token_secret: ACCESS_TOKEN_SECRET
});
const mlbStats = new MLBStatsAPI();
const RDS = new AWS.RDSDataService()

let HIT_DB = false

function prepString(s){
    return `'${s.toString().replace("'","''")}'`
}

function updateDB(data){
    let tasks = []
    for(let r = 0; r < data.length; r++){
        if(data[r].strikeouts >= 3){
            HIT_DB = true

            let x = new Promise((res,rej) => {
                
                let query = `INSERT INTO "sombrero"(${Object.keys(data[r]).join()})
                VALUES (${Object.values(data[r]).map(s => prepString(s)).join()})
                ON CONFLICT (id) DO
                UPDATE SET tweeted=FALSE WHERE EXCLUDED.strikeouts!=${data[r].strikeouts}; INSERT INTO "sombrero"(${Object.keys(data[r]).join()})
                VALUES (${Object.values(data[r]).map(s => prepString(s)).join()})
                ON CONFLICT (id) DO
                UPDATE SET strikeouts=${data[r].strikeouts};`
                
                // console.log(query)
                
                
                const params = {
                    secretArn: DB_SECRET_ARN,
                    resourceArn: DB_RESOURCE_ARN,
                    sql: query,
                    database: DB_NAME
                }
                
                console.log('updating sombrero records in DB')
                RDS.executeStatement(params,(err,data)=>{
                    if(err){
                        rej(err)
                    } else {
                        res(data)
                    }
                    
                })
            })
            tasks.push(x)
        }
    }
    return tasks
}

function getSombreros(){
    return new Promise((res,rej) => {
        let query = `SELECT * FROM "sombrero" WHERE strikeouts >= 3 AND tweeted = FALSE`

        const params = {
            secretArn: DB_SECRET_ARN,
            resourceArn: DB_RESOURCE_ARN,
            sql: query,
            includeResultMetadata:true,
            database: DB_NAME
        }
        
        console.log('pulling fresh sombreros from DB')
        RDS.executeStatement(params,(err,data)=>{
            if(err){
                rej(err)
            } else {
                res(data)
            }
            
        })
    })
}

function markTweeted(data){
    return new Promise((res,rej) => {
        let query = `INSERT INTO "sombrero"(${Object.keys(data).join()})
        VALUES (${Object.values(data).map(s => prepString(s)).join()})
        ON CONFLICT (id) DO
        UPDATE SET tweeted=TRUE`

        // console.log(query)

        const params = {
            secretArn: DB_SECRET_ARN,
            resourceArn: DB_RESOURCE_ARN,
            sql: query,
            includeResultMetadata:true,
            database: DB_NAME
        }
        
        console.log('updating rows that were tweeted out')
        RDS.executeStatement(params,(err,data)=>{
            if(err){
                rej(err)
            } else {
                res(data)
            }
            
        })
    })
}

function tweetSombrero(columns,data){
    let obj = {}
    for(let c = 0; c < columns.length; c++){
        obj[columns[c].name] = Object.values(data[c])[0]
    }

    let sombrero = obj.sombrero ? (parseInt(obj.strikeouts) > 4 ? 'PLATINUM SOMBRERO: ' : 'GOLDEN SOMBRERO: ') : 'SOMBRERO WATCH: '

    let tweet = `${sombrero}${obj.name} has struck out ${parseInt(obj.strikeouts)} times (${obj.team} vs. ${obj.opponent})`
    console.log(obj, tweet)
    T.post('statuses/update', { status: tweet }, function(err, d, response) {
        if(err){
            console.log(err)
        }
      })
    markTweeted(obj)
}


function getTodaysGames(schedule){
    let dates = schedule.dates
    let today = new Date()
    let gamesToCheck = []

    for(let d = 0; d < dates.length; d++){
        if(today - new Date(dates[d].date) <= 86400000*2){
            gamesToCheck.push(...schedule.dates[d].games)
        }
    }
    return gamesToCheck
}

// take list of playerIDs who struck out, return {id:count}
function reduceStrikeoutList(list){
  var initialValue = {}
  var reducer = function(count, player) {
    if (!count[player.id]) {
        count[player.id] = {
            ...player
        }
        count[player.id].strikeouts = 1;
    } else {
      count[player.id].strikeouts = count[player.id].strikeouts + 1;
    }
    return count;
  }
  return list.reduce(reducer, initialValue)
}

// async function getPlayerAtBats(playerID,gameID){
//     console.log(playerID,gameID)
//     const req = await mlbStats.getPersonStats({pathParams:{'personId':playerID,'gamePk':gameID}})
//     console.log(req.url)
//     return 1
// }

function getStrikeoutsFromGame(plays, gameInfo){
    let homeTeam = gameInfo.teams.home.team.name
    let awayTeam = gameInfo.teams.away.team.name
    let venue = gameInfo.venue.name
    let date = gameInfo.officialDate

    let K = plays.filter(d => d.result.eventType === 'strikeout')
        .map(d => {
            return {
                name:d.matchup.batter.fullName,
                id:d.matchup.batter.id,
                team:d.about.isTopInning ? awayTeam : homeTeam,
                opponent: d.about.isTopInning ? homeTeam : awayTeam,
            }
        })
    
    if(K.length > 0){
        let rawCounts = reduceStrikeoutList(K)
        let countsWithInfo = Object.keys(rawCounts).map(d => {
            return {
                ...rawCounts[d],
                playerid: d,
                gameid: gameInfo.gamePk,
                id:`${d}${gameInfo.gamePk}`,
                venue:venue,
                date:date,
                sombrero:rawCounts[d] >= 4 ? 'TRUE' : 'FALSE'
            }
        })

        // for players who have struck out, get their current number of at-bats
        // for(let i = 0; i < countsWithInfo.length; i++){
        //     countsWithInfo.abs = await getPlayerAtBats(countsWithInfo[i].playerId,gameInfo.gamePk)
        // }
        // console.log(countsWithInfo)
        return countsWithInfo
    } else return []
}



    // const response = await mlbStats.getScheduleTied({params:{'season':'2020'}});
    // get all games on schedule
    let response
    try{
        response = await mlbStats.getSchedule({params:{'sportId':1}});
    }
    catch (error) {
        console.error(error)
    }
    const schedule = await response.data

    // only keep games within the last 24 hours
    let gamesToCheck = getTodaysGames(schedule)
    console.log(`checking ${gamesToCheck.length} games`)

    let allPlayerKCounts = []

    for(let g = 0; g < gamesToCheck.length; g++){
        console.log(gamesToCheck[g].gamePk)

        // get play by play for each game
        const gameResponse = await mlbStats.getGamePlayByPlay({pathParams:{gamePk:gamesToCheck[g].gamePk}})

        // get per batter strikeout count for each game
        let playerKCounts = await getStrikeoutsFromGame(gameResponse.data.allPlays, gamesToCheck[g])

        console.log(`${playerKCounts.length} players with strikeouts`)
        allPlayerKCounts.push(...playerKCounts)
    }
    
    console.log(`TOTAL: ${allPlayerKCounts.length} players`)
    await Promise.all(updateDB(allPlayerKCounts))
        .then(()=>{
            if(HIT_DB){
                return getSombreros()
            } else {
                console.log('skipping DB, nobody close')
                return []
            }
        })
        .then(d => {
            if(d.records){

                console.log(`Tweeting ${d.records.length} sombrero watches`)
                for(let i = 0; i < d.records.length; i++){
                    tweetSombrero(d.columnMetadata,d.records[i])
                }
            } else console.log('no tweets to send')
        })

    // return {
    //     statusCode: 200,
    //     body: JSON.stringify(
    //         {
    //             message: 'Go Serverless v1.0! Your function executed successfully!',
    //             input: event,
    //         },
    //         null,
    //         2
    //     ),
    // };

    // Use this code if you don't use the http event with the LAMBDA-PROXY integration
    return { message: 'Finished', event };
};
