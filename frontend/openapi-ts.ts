import { createClient } from '@hey-api/openapi-ts';

createClient({
    client: '@hey-api/client-axios',
    input: 'http://localhost:8000/openapi.json',
    output: './src/lib/client',
});