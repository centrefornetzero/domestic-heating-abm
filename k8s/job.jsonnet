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
            args: args_excl_output + [
              '--bigquery',
              "select * from %s.prod_domestic_heating.household_agents where abs(mod(farm_fingerprint(id), 307)) = 1 and occupant_type != 'rented_social'" % std.extVar('PROJECT_ID'),
              'gs://%s/%s/{uuid}/output.jsonl.gz' % [std.extVar('BUCKET_NAME'), name],
            ],
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

[
  // scenarios
  job('01a-%s-max-policy-extended-bus' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'extended_boiler_upgrade_scheme',
    '--intervention',
    'heat_pump_campaign',
    '--campaign-target-heat-pump-awareness-date',
    '2028-01-01:0.5',
    '--campaign-target-heat-pump-awareness-date',
    '2034-01-01:0.75',
    '--intervention',
    'gas_oil_boiler_ban',
    '--gas-oil-boiler-ban-date',
    '2035-01-01',
    '--gas-oil-boiler-ban-announce-date',
    '2025-01-01',
    '--heat-pump-awareness',
    '0.25',
    '--price-gbp-per-kwh-gas',
    '0.0682',
    '--price-gbp-per-kwh-electricity',
    '0.182',
    '--heat-pump-installer-count',
    '10000000000'
  ]),
  job('01b-%s-max-policy-extended-bus' % std.extVar('SHORT_SHA'), [
    '--intervention',
    'extended_boiler_upgrade_scheme',
    '--intervention',
    'heat_pump_campaign',
    '--campaign-target-heat-pump-awareness-date',
    '2028-01-01:0.75',
    '--intervention',
    'gas_oil_boiler_ban',
    '--gas-oil-boiler-ban-date',
    '2035-01-01',
    '--gas-oil-boiler-ban-announce-date',
    '2025-01-01',
    '--heat-pump-awareness',
    '0.5',
    '--price-gbp-per-kwh-gas',
    '0.0682',
    '--price-gbp-per-kwh-electricity',
    '0.182',
    '--heat-pump-installer-count',
    '10000000000'
  ]),
]
