const vendors = require('../../data/vendors.json');

module.exports = {

    token: function (req, res) {
        const clientId = req.body.client_id;
        const clientSecret = req.body.client_secret;

        if (clientId !== 'pv-client' || clientSecret !== 'pv-secret') {
            sails.log.info('POST /token - 401');

            return res.status(401).json({
                error: 'Invalid client credentials'
            });
        }

        const accessToken = TokenService.createToken();

        sails.log.info('POST /token - 200');

        return res.json({
            access_token: accessToken,
            expires_in: 3600
        });
    },


    listVendors: function (req, res) {
        const offset = parseInt(req.query.offset || 0);
        const limit = parseInt(req.query.limit || 50);

        const items = vendors.slice(offset, offset + limit);

        const hasMore = offset + limit < vendors.length;

        sails.log.info('GET /vendors - 200');

        return res.json({
            items: items,
            offset: offset,
            limit: limit,
            hasMore: hasMore
        });
    },


    createDan: function (req, res) {
        const vendorId = req.body.VENDOR_ID;
        const amount = req.body.AMOUNT;
        const danDate = req.body.DAN_DATE;

        if (!vendorId) {
            sails.log.info('POST /dan - 400');

            return res.status(400).json({
                status: 'ERROR',
                message: 'VENDOR_ID is required'
            });
        }

        if (!amount) {
            sails.log.info('POST /dan - 400');

            return res.status(400).json({
                status: 'ERROR',
                message: 'AMOUNT is required'
            });
        }

        if (!danDate) {
            sails.log.info('POST /dan - 400');

            return res.status(400).json({
                status: 'ERROR',
                message: 'DAN_DATE is required'
            });
        }

        const danId = 'DAN-2026-' + Math.floor(100000 + Math.random() * 900000);

        sails.log.info('POST /dan - 200');

        return res.json({
            status: 'SUCCESS',
            id: danId
        });
    },


    createUnit: function (req, res) {
        if (req.body.LINE_NO === 2) {
            sails.log.info('POST /units - 400 (forced failure for line 2)');

            return res.status(400).json({
                status: 'ERROR',
                message: 'Forced failure for testing line 2'
            });
        }

        const unitId = 'UNIT-' + Math.floor(100000 + Math.random() * 900000);

        sails.log.info('POST /units - 200');

        return res.json({
            status: 'SUCCESS',
            id: unitId
        });
    }
};