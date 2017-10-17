from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://data.doremus.org/sparql")
sparql.setQuery("""
SELECT DISTINCT ?expression WHERE { 
 ?complexWork mus:U38_has_descriptive_expression ?expression 
}""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

with open("all_expressions.txt", "w") as wf:
  for result in results["results"]["bindings"]:
    wf.write(result["expression"]["value"]+"\n")

print("done")
