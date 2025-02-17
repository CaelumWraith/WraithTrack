# emulates the following curl requests:
#curl -X POST "https://accounts.spotify.com/api/token" \
#     -H "Content-Type: application/x-www-form-urlencoded" \
#     -d "grant_type=client_credentials&client_id=your-client-id&client_secret=your-client-secret"
# and with bearer token:
#curl -X GET "https://api.spotify.com/v1/artists/16SiO2DZeffJZAKlppdOAw" \
#     -H "Authorization: Bearer {your_access_token}"