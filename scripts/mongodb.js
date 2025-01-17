const { MongoClient } = require('mongodb');
const fs = require('fs');

// Connection URL
const url = 'mongodb://localhost:27017';
const client = new MongoClient(url);

// Database Name
const dbName = 'oceanDubaiHackathon';

async function main() {
    // Use connect method to connect to the server
    await client.connect();
    console.log('Connected successfully to server');
    const db = client.db(dbName);
    const collection = db.collection('properties');

    // Read dataset from file
    const data = JSON.parse(fs.readFileSync('path/to/your/dataset.json', 'utf8'));

    // Insert dataset into collection
    const insertResult = await collection.insertMany(data);
    console.log('Inserted documents =>', insertResult);

    // Close connection
    await client.close();
}

main().catch(console.error);