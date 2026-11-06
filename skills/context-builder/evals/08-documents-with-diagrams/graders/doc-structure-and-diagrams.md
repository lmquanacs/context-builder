Grade `charging.md` as a document for readers who don't read code.

Pass requires all of:

1. **Correct behaviour, two layers.** The document makes clear that one charge
   can send several requests because there are two retries, one inside the
   other:
   - the charge itself is tried up to 3 times when the payment service answers
     "not OK" (`src/billing/charge.ts`);
   - each of those tries retries its network request up to 3 times on a
     connection error, waiting a little longer each time
     (`src/http/client.ts`, `src/config/settings.ts`);
   - so a single charge can send up to 9 requests.
   A document that shows only one retry layer fails, because it doesn't answer
   the support team's question.
2. **Structure.** It has a plain-language summary first, then a
   step-by-step "how it works", and at least two of: at a glance, key parts,
   configuration, errors or troubleshooting, glossary. No empty or "N/A"
   sections.
3. **Diagrams.** At least two diagrams: an overview (context diagram or mind
   map) and a flow (flowchart or sequence diagram) that shows both retry
   layers. Each has a caption that states the takeaway (e.g. "One charge can
   send up to 9 requests"), not just a topic ("Charge flow").
4. **Easy to read.** Diagram boxes use plain words ("Try the payment again"),
   not code names like `fetchWithRetry` or `policy.attempts`. Each flow
   diagram has numbered steps and a numbered walkthrough in words underneath.
   No diagram has more than about nine boxes.
5. **Nothing invented.** No solid box or arrow shows behaviour the fixture
   doesn't contain: emails, refunds triggered by failure, card-decline codes,
   or a circuit breaker. Unconfirmed steps are left out or clearly marked.
6. **Valid Mermaid** (if Mermaid is used): each block would parse, i.e. no
   unquoted parentheses or colons in labels and no node called `end`.

Fail on a wall of prose with no diagram, on diagrams labelled with function
names, or on a correct-looking diagram that contradicts the code.
