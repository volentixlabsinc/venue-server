const {inputRequired} = require('./utils');

module.exports = plop => {
  plop.setGenerator('role', {
    prompts: [
      {
        type: 'input',
        name: 'namespace',
        message: 'Namespace.',
        validate: inputRequired('namespace')
      },
      {
        type: 'input',
        name: 'postgress-external-name',
        message: 'Postgress External Name',
        validate: inputRequired('postgress-external-name')
      }
    ],
    actions: [
      {
        type: 'add',
        path: '../generated/{{namespace}}/0.0.namespace.yml',
        templateFile: 'templates/0.0.namespace.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/0.1.serviceaccount.yml',
        templateFile: 'templates/0.1.serviceaccount.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/1.0.default-backend.yml',
        templateFile: 'templates/1.0.default-backend.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/1.1.postgres.yml',
        templateFile: 'templates/1.1.postgres.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/1.2.secrets.yml',
        templateFile: 'templates/1.2.secrets.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/1.3.redis.yml',
        templateFile: 'templates/1.3.redis.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/2.0.api.deployment.yml',
        templateFile: 'templates/2.0.api.deployment.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/2.1.api.service.yml',
        templateFile: 'templates/2.1.api.service.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/2.2.api.ingress.yml',
        templateFile: 'templates/2.2.api.ingress.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/3.0.ui.deployment.yml',
        templateFile: 'templates/3.0.ui.deployment.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/3.1.ui-service.yml',
        templateFile: 'templates/3.1.ui-service.template'
      },{
        type: 'add',
        path: '../generated/{{namespace}}/3.2.ui.ingress.yml',
        templateFile: 'templates/3.2.ui.ingress.template'
      }      
    ]
  });
};

