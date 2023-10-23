const fs = require("fs");

//from console, run "node noteWallcleaner YOUR_JSON_FILE"
//it strips out everything except username and message
//and prints to console

    const json = fs.readFileSync(process.argv[2]);
    const raw = JSON.parse(json);
    
    const stripped = raw.map(note => {
        return ({
            author: note.authorUsername,
            message: note.message
        })
    })
    
    console.log(JSON.stringify(stripped));