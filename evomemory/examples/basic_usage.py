from evomemory import EvoMemory

mem = EvoMemory("my_business_agent")

mem.add("Q1 revenue goal: $47k", mem_type="goal", importance=0.95)
results = mem.search("revenue", k=3)
print(results)
