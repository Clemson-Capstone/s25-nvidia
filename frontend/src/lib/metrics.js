const client = require('prom-client');

// Create a Registry to register the metrics
const register = new client.Registry();

// Add a default label which is added to all metrics
register.setDefaultLabels({
  app: 'nextjs-app'
});

// Enable the collection of default metrics
client.collectDefaultMetrics({ register });

// Create a custom metric for API calls if you need one
const apiCallsCounter = new client.Counter({
  name: 'api_calls_total',
  help: 'Total number of API calls',
  labelNames: ['method', 'endpoint', 'status']
});

// Register the custom metrics
register.registerMetric(apiCallsCounter);

module.exports = {
  register,
  apiCallsCounter
};