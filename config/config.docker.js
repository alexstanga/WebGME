var config = require('./config.default'),
    validateConfig = require('webgme/config/validator');

config.mongo.uri = 'mongodb://mongo:27017/micproject';

validateConfig(config);
module.exports = config;