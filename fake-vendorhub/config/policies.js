/**
 * Policy Mappings
 * (sails.config.policies)
 *
 * Policies are simple functions which run **before** your actions.
 *
 * For more information on configuring policies, check out:
 * https://sailsjs.com/docs/concepts/policies
 */

module.exports.policies = {

   VendorHubController: {

        token: [
            'randomFailure'
        ],

        listVendors: [
            'randomFailure',
            'checkToken'
        ],

        createDan: [
            'randomFailure',
            'checkToken'
        ],

        createUnit: [
            'randomFailure',
            'checkToken'
        ]

    }
};
