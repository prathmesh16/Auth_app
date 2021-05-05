
var MongoClient = require('mongodb').MongoClient;
var dburl = "mongodb://localhost:27017/";

function checkUserExist(username,password,callback)
{
    MongoClient.connect(dburl, function(err, db) {
        if (err) throw err;
        var dbo = db.db("mydb");
        var query = { username:username,password:password };
        dbo.collection("users").find(query).toArray(function(err, result) {
            if (result.length==0)
            {
                console.log("user not exists");
                callback(false)
            }
            else
            {
                console.log("user exists");
                callback(true);
            }
            db.close();
        });
      });
}

function fetchUser(username,password,callback)
{
    MongoClient.connect(dburl, function(err, db) {
        if (err) throw err;
        var dbo = db.db("mydb");
        var query = { username:username,password:password };
        dbo.collection("users").find(query).toArray(function(err, result) {
            if (result.length==0)
            {
                console.log("user not exists");
                callback(null)
            }
            else
            {
                console.log("user exists");
                callback(result[0]);
            }
            db.close();
        });
      });
}

function addUser(user,callback)
{
    MongoClient.connect(dburl, function(err, db) {
        if (err) throw err;
        var dbo = db.db("mydb");
        var query = { username:user.username};
        dbo.collection("users").find(query).toArray(function(err, result) {
            if (result.length==0)
            {
                MongoClient.connect(dburl, function(err, db) {
                    if (err) throw err;
                    var dbo = db.db("mydb");
                    dbo.collection("users").insertOne(user, function(err, res) {
                        if (err)
                            callback(false,"User not inserted,User already exists with this username")
                        else
                            callback(true,"user inserted")
                      db.close();
                    });
                });
            }
            else
            {
                callback(false,"User not inserted,User already exists with this username")
            }
            db.close();
        });
      });
    
}

module.exports = {
    checkUserExist,
    fetchUser,
    addUser
}