const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'OpenPolicy Platform API',
      version: '4.0.0',
      description: 'Comprehensive API documentation for OpenPolicy Platform V4',
      termsOfService: 'https://openpolicy.com/terms',
      contact: {
        name: 'API Support',
        url: 'https://openpolicy.com/support',
        email: 'api@openpolicy.com'
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT'
      }
    },
    servers: [
      {
        url: 'http://localhost:9000/api',
        description: 'Development server'
      },
      {
        url: 'https://api.openpolicy.com',
        description: 'Production server'
      }
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT'
        },
        apiKey: {
          type: 'apiKey',
          in: 'header',
          name: 'X-API-Key'
        }
      },
      schemas: {
        Error: {
          type: 'object',
          properties: {
            code: { type: 'integer' },
            message: { type: 'string' },
            details: { type: 'object' }
          }
        },
        Policy: {
          type: 'object',
          properties: {
            id: { type: 'string', format: 'uuid' },
            title: { type: 'string' },
            description: { type: 'string' },
            category: { type: 'string' },
            status: { type: 'string', enum: ['draft', 'active', 'archived'] },
            created_at: { type: 'string', format: 'date-time' },
            updated_at: { type: 'string', format: 'date-time' }
          }
        },
        Bill: {
          type: 'object',
          properties: {
            id: { type: 'string', format: 'uuid' },
            number: { type: 'string' },
            title: { type: 'string' },
            sponsor: { type: 'string' },
            status: { type: 'string' },
            introduced_date: { type: 'string', format: 'date' }
          }
        },
        Representative: {
          type: 'object',
          properties: {
            id: { type: 'string', format: 'uuid' },
            name: { type: 'string' },
            party: { type: 'string' },
            district: { type: 'string' },
            email: { type: 'string', format: 'email' },
            phone: { type: 'string' }
          }
        }
      }
    },
    security: [{
      bearerAuth: []
    }]
  },
  apis: ['./services/*/routes/*.js', './services/*/controllers/*.js']
};

const specs = swaggerJsdoc(options);

module.exports = { swaggerUi, specs };