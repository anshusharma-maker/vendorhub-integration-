module.exports = function (req, res, next) {

    const failRate = parseFloat(process.env.FAIL_RATE || 0);

    const randomNumber = Math.random();

    if (randomNumber < failRate) {
        sails.log.info(`${req.method} ${req.url} - 503`);

        return res.status(503).json({
            error: 'VendorHub temporarily unavailable'
        });
    }

    return next();
};