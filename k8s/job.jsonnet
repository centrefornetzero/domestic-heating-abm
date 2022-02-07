local job(name, args_excl_output) = {
  apiVersion: 'batch/v1',
  kind: 'Job',
  metadata: {
    name: name,
    namespace: 'domestic-heating-abm',
  },
  spec: {
    completions: 10,
    parallelism: 5,
    template: {
      spec: {
        containers: [
          {
            name: 'domestic-heating-abm',
            image: std.extVar('IMAGE_URI'),
            command: ['python', '-m', 'simulation'],
            args: args_excl_output + ['gs://%s/%s/{uuid}/output.jsonl.gz' % [std.extVar('BUCKET_NAME'), name]],
            env: [
              { name: 'PROJECT_ID', value: std.extVar('PROJECT_ID') },
            ],
            resources: {
              requests: {
                memory: '1024Mi',
                cpu: '1000m',
              },
            },
          },
        ],
        restartPolicy: 'Never',
        serviceAccountName: 'runner',
      },
    },
  },
};

local bigquery_arg = [
  '--bigquery',
  'select * from %s.prod_domestic_heating.dim_household_agents where abs(mod(farm_fingerprint(id), 307)) = 1' % std.extVar('PROJECT_ID'),
];

[
  // scenarios

  job('01-%s-rhi' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'rhi',
    '--start-date',
    '2012-01-01',
    '--steps',
    '120',
    '--heat-pump-installer-annual-growth-rate',
    '0',
  ] + bigquery_arg),
  job('02-%s-baseline' % std.extVar('SHORT_SHA'), [
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
  ] + bigquery_arg),
  job('03a-%s-bus' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
  ] + bigquery_arg),
  job('03b-%s-bus-policy' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--price-gbp-per-kwh-gas',
    '0.0685',
    '--price-gbp-per-kwh-electricity',
    '0.1656',
    '--price-gbp-per-kwh-oil',
    '0.0702',
  ] + bigquery_arg),
  job('03c-%s-bus-policy-high-awareness' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--heat-pump-awareness',
    '0.5',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--price-gbp-per-kwh-gas',
    '0.0685',
    '--price-gbp-per-kwh-electricity',
    '0.1656',
    '--price-gbp-per-kwh-oil',
    '0.0702',
  ] + bigquery_arg),
  job('04a-%s-max-policy' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--intervention',
    'gas_oil_boiler_ban',
    '--gas-oil-boiler-ban-date',
    '2035-01-01',
    '--gas-oil-boiler-ban-announce-date',
    '2025-01-01',
    '--heat-pump-awareness',
    '0.5',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--price-gbp-per-kwh-gas',
    '0.0685',
    '--price-gbp-per-kwh-electricity',
    '0.1656',
    '--price-gbp-per-kwh-oil',
    '0.0702',
  ] + bigquery_arg),
  job('04b-%s-max-policy-delayed-announcement' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--intervention',
    'gas_oil_boiler_ban',
    '--gas-oil-boiler-ban-date',
    '2035-01-01',
    '--gas-oil-boiler-ban-announce-date',
    '2030-01-01',
    '--heat-pump-awareness',
    '0.5',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--price-gbp-per-kwh-gas',
    '0.0685',
    '--price-gbp-per-kwh-electricity',
    '0.1656',
    '--price-gbp-per-kwh-oil',
    '0.0702',
  ] + bigquery_arg),
  job('05-%s-max-industry' % std.extVar('SHORT_SHA'), [
    '--heat-pump-awareness',
    '0.5',
    '--heating-system-hassle-factor',
    '0',
    '--all-agents-heat-pump-suitable',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--air-source-heat-pump-price-discount-date',
    '2025-01-01:0.6',
  ] + bigquery_arg),
  job('06-%s-max-policy-max-industry' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--intervention',
    'gas_oil_boiler_ban',
    '--gas-oil-boiler-ban-announce-date',
    '2025-01-01',
    '--gas-oil-boiler-ban-date',
    '2030-01-01',
    '--heat-pump-awareness',
    '0.5',
    '--heating-system-hassle-factor',
    '0',
    '--all-agents-heat-pump-suitable',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--air-source-heat-pump-price-discount-date',
    '2025-01-01:0.6',
    '--price-gbp-per-kwh-gas',
    '0.0685',
    '--price-gbp-per-kwh-electricity',
    '0.1656',
    '--price-gbp-per-kwh-oil',
    '0.0702',
  ] + bigquery_arg),

  // sensitivity tests

  job('50-%s-pump-awareness-low' % std.extVar('SHORT_SHA'), [
    '--heat-pump-awareness',
    '0.2',
  ] + bigquery_arg),
  job('51-%s-pump-awareness-high' % std.extVar('SHORT_SHA'), [
    '--heat-pump-awareness',
    '1.0',
  ] + bigquery_arg),

  job('52-%s-annual-reno-rate-low' % std.extVar('SHORT_SHA'), [
    '--annual-renovation-rate',
    '0.05',
  ] + bigquery_arg),
  job('53-%s-annual-reno-rate-high' % std.extVar('SHORT_SHA'), [
    '--annual-renovation-rate',
    '0.33',
  ] + bigquery_arg),

  job('54-%s-household-lookahead-low' % std.extVar('SHORT_SHA'), [
    '--household-num-lookahead-years',
    '1',
  ] + bigquery_arg),
  job('55-%s-household-lookahead-high' % std.extVar('SHORT_SHA'), [
    '--household-num-lookahead-years',
    '5',
  ] + bigquery_arg),
  
  job('56-%s-heating-system-hassle-low' % std.extVar('SHORT_SHA'), [
    '--heating-system-hassle-factor',
    '0',
  ] + bigquery_arg),
  job('57-%s-heating-system-hassle-high' % std.extVar('SHORT_SHA'), [
    '--heating-system-hassle-factor',
    '0.2',
  ] + bigquery_arg),

  job('58-%s-heat-pump-suitable-low' % std.extVar('SHORT_SHA'), bigquery_arg),
  job('59-%s-heat-pump-suitable-high' % std.extVar('SHORT_SHA'), [
    '--all-agents-heat-pump-suitable',
  ] + bigquery_arg),

  job('59-%s-gas-price-low' % std.extVar('SHORT_SHA'), [
    '--price-gbp-per-kwh-gas',
    '0.02325',
  ] + bigquery_arg),
  job('60-%s-gas-price-high' % std.extVar('SHORT_SHA'), [
    '--price-gbp-per-kwh-gas',
    '0.06975',
  ] + bigquery_arg),

  job('61-%s-electricity-price-low' % std.extVar('SHORT_SHA'), [
    '--price-gbp-per-kwh-electricity',
    '0.1003',
  ] + bigquery_arg),
  job('62-%s-electricity-price-high' % std.extVar('SHORT_SHA'), [
    '--price-gbp-per-kwh-electricity',
    '0.3009',
  ] + bigquery_arg),

  job('63-%s-oil-price-low' % std.extVar('SHORT_SHA'), [
    '--price-gbp-per-kwh-oil',
    '0.0241',
  ] + bigquery_arg),
  job('64-%s-oil-price-high' % std.extVar('SHORT_SHA'), [
    '--price-gbp-per-kwh-oil',
    '0.0723',
  ] + bigquery_arg),

  job('65-%s-ashp-discount-low' % std.extVar('SHORT_SHA'), [
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0',
  ] + bigquery_arg),
  job('66-%s-ashp-discount-high' % std.extVar('SHORT_SHA'), [
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.6',
  ] + bigquery_arg),

  job('67-%s-hp-installer-growth-low' % std.extVar('SHORT_SHA'), [
    '--heat-pump-installer-annual-growth-rate',
    '0',
  ] + bigquery_arg),
  job('68-%s-hp-installer-growth-high' % std.extVar('SHORT_SHA'), [
    '--heat-pump-installer-annual-growth-rate',
    '1',
  ] + bigquery_arg),
]
