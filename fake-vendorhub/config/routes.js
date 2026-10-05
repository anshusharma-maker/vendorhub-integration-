/**
 * Route Mappings
 * (sails.config.routes)
 *
 * Your routes tell Sails what to do each time it receives a request.
 *
 * For more information on configuring custom routes, check out:
 * https://sailsjs.com/anatomy/config/routes-js
 */

module.exports.routes = {
    'post /token': 'VendorHubController.token', 
    'get /vendors': 'VendorHubController.listVendors', 
    'post /dan': 'VendorHubController.createDan', 
    'post /units': 'VendorHubController.createUnit', 


};
