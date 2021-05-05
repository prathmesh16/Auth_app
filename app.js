const express = require('express')
const jwt = require('jsonwebtoken')
const url = require('url')
var cors = require('cors')
const app = express()
const port = 3000
app.use(cors()) 
const db = require('./database')

app.use(express.urlencoded({extended:true}));
app.use(express.json());

app.set('views', __dirname + '/views');
app.engine('html', require('ejs').renderFile);

function checkUserExist(username , password , callback)
{
    db.checkUserExist(username,password,callback)
}
app.get('/getUser',(req,res)=>{
    var url = new URL(req.protocol + "://" + req.get('host') + req.originalUrl);
    var token = url.searchParams.get('token');
    jwt.verify(token, 'prathmeshLoginServer', function(err, decoded) {
        // err
        if(err)
        {
            res.send({success:false});
        }
        else
        {
            db.fetchUser(decoded.username,decoded.password,(result)=>{
                res.send({success:true,user:result})    
            })
        }
      });
})
app.get('/homepage',(req,res)=>{

    var url = new URL(req.protocol + "://" + req.get('host') + req.originalUrl);
    var name = url.searchParams.get('name');

    res.render('homepage.html',{name:name})
})
app.get('/verifyToken',(req,res)=>{
    var url = new URL(req.protocol + "://" + req.get('host') + req.originalUrl);
    var token = url.searchParams.get('token');
    jwt.verify(token, 'prathmeshLoginServer', function(err, decoded) {
        // err
        if(err)
        {
            res.send({success:false});
        }
        else
        {
            console.log(decoded);
            res.send({success:true,name:decoded.username})
        }
      });
})
app.post('/verify',(req,res)=>{
    checkUserExist(req.body.name,req.body.pass,(result)=>{
        if(result)
        {
            var token = jwt.sign({ username:req.body.name,password:req.body.pass }, 'prathmeshLoginServer', { expiresIn: 60 * 60 });
            res.redirect('/homepage?name='+req.body.name+'&&token='+token)
        }
        else
        {
            res.redirect('/login?err=true')
        }
    })
   
})
app.get('/',(req,res)=>{
    res.redirect('/login');
})
app.get('/login', (req, res) => {
    console.log(req.url);

    var url = new URL(req.protocol + "://" + req.get('host') + req.originalUrl);
    var err = url.searchParams.get('err');
    
    res.render('login.html',{err:err})    
})

app.get('/signup',(req,res)=>{
    res.render("signup.html");
})

app.post('/addUser',(req,res)=>{
    var user = {
        username:req.body.name,
        password:req.body.pass
    }
    db.addUser(user,(success,result)=>{
        res.send({success:success,message:result});
    })
})

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})