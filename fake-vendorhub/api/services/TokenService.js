const crypto = require('crypto');

const tokens = {};

module.exports = {

    createToken: function () {
        const token = crypto.randomBytes(24).toString('hex');

        tokens[token] = {
            expiresAt: Date.now() + 3600 * 1000
        };

        return token;
    },

    isValid: function (token) {
        const tokenData = tokens[token];

        if (!tokenData) {
            return false;
        }

        if (Date.now() > tokenData.expiresAt) {
            delete tokens[token];
            return false;
        }

        return true;
    }

};