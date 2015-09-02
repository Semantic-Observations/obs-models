for q in *.rq; do
  echo "QUERY: $q"
  for f in *.owl; do
    echo "ONTOLOGY: $f"
    sparql --query $q --data=$f --time
  done
  echo ""
done
