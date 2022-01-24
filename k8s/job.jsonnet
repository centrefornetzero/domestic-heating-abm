local job(name, args_excl_output) = {
  apiVersion: 'batch/v1',
  kind: 'Job',
  metadata: {
    name: name,
    namespace: 'domestic-heating-abm',
  },
  spec: {
    template: {
      spec: {
        containers: [
          {
            name: 'domestic-heating-abm',
            image: std.extVar('IMAGE_URI'),
            command: ['python', '-m', 'simulation'],
            args: args_excl_output + ['gs://%s/%s/{uuid}/output.jsonl' % [std.extVar('BUCKET_NAME'), name]],
            env: [
              { name: 'PROJECT_ID', value: std.extVar('PROJECT_ID') },
            ],
          },
        ],
        restartPolicy: 'Never',
        nodeSelector: {
          'cloud.google.com/gke-spot': 'true',
        },
        serviceAccountName: 'runner',
      },
    },
  },
};

local bigquery_arg = [
  '--bigquery',
  'select * from %s.prod_domestic_heating.dim_household_agents limit 1000' % std.extVar('PROJECT_ID'),
];

[
  job('01-%s-baseline' % std.extVar('SHORT_SHA'), [
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
  ] + bigquery_arg),
  job('02-%s-bus' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
  ] + bigquery_arg),
  job('03-%s-bus_policy' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--gas-gbp-per-kwh',
    '0.0685',
    '--elec-gbp-per-kwh',
    '0.1656',
    '--oil-gbp-per-kwh',
    '0.0702',
  ] + bigquery_arg),
  job('04-%s-bus_policy_high_awareness' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--heat-pump-awareness',
    '0.6',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--gas-gbp-per-kwh',

    '0.0685',
    '--elec-gbp-per-kwh',
    '0.1656',
    '--oil-gbp-per-kwh',
    '0.0702',
  ] + bigquery_arg),
  job('05-%s-max_policy' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--intervention',
    'boiler_ban',
    '--gas-oil-boiler-ban-date',
    '2030-01-01',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--gas-gbp-per-kwh',
    '0.0685',
    '--elec-gbp-per-kwh',
    '0.1656',
    '--oil-gbp-per-kwh',
    '0.0702',
  ] + bigquery_arg),
  job('06-%s-max_industry' % std.extVar('SHORT_SHA'), [
    '--heating-system-hassle-factor',
    '0.1',
    '--all-agents-heat-pump-suitable',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--air-source-heat-pump-price-discount-date',
    '2025-01-01:0.5',
  ] + bigquery_arg),
  job('07-%s-max_policy_max_industry' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'boiler_upgrade_scheme',
    '--intervention',
    'boiler_ban',
    '--gas-oil-boiler-ban-date',
    '2030-01-01',
    '--heat-pump-awareness',
    '0.6',
    '--heating-system-hassle-factor',
    '0',
    '--all-agents-heat-pump-suitable',
    '--air-source-heat-pump-price-discount-date',
    '2023-01-01:0.3',
    '--air-source-heat-pump-price-discount-date',
    '2025-01-01:0.5',
    '--gas-gbp-per-kwh',
    '0.0685',
    '--elec-gbp-per-kwh',
    '0.1656',
    '--oil-gbp-per-kwh',
    '0.0702',
  ] + bigquery_arg),
]
