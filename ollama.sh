query=$(cat prompt.txt)
activities=$(cat events.md)
final_query="$query$activities"
final_query=$(echo $final_query | tr -d '\n')
echo $final_query | clip.exe
curl localhost:11434/api/generate -d "{
  \"model\":\"deepseek-r1-32k\",
  \"prompt\":\"$final_query\"
}" | jq -rj ".response" > llama-out.txt

#echo $(echo $response | tr -d "\"")
