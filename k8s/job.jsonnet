{
  apiVersion: 'batch/v1',
  kind: 'Job',
  metadata: {
    name: std.extVar('JOB_NAME'),
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
            args: ['--bigquery', 'select * from %s.prod_domestic_heating.dim_household_agents limit 1000' % std.extVar('PROJECT_ID'), 'gs://%/{uuid}/output.jsonl' % std.extVar('BUCKET_NAME')],
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
}
