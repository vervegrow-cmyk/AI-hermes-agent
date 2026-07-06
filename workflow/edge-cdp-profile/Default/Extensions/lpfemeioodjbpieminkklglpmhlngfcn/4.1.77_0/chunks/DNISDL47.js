import{a as m}from"./JV43EUJH.js";import{b as d,t as r,y as p}from"./E4I5EUY3.js";import{a as T}from"./UX5Z4UUX.js";import{g as f}from"./BUHNM4FS.js";import{f as i}from"./3PS7M655.js";var g=[{title:"Free AI",titleTag:"",value:"mistral-7b-instruct",maxTokens:4096,tags:[],descriptions:[{label:"client:provider__model__tooltip_card__label__max_token",value:"client:provider__model__tooltip_card__label__max_token__suffix"},{label:"client:provider__model__tooltip_card__label__description",value:"client:provider__chatgpt__model__gpt_3_5__description"}]}];var v=[{title:"PaLM 2",titleTag:"",value:"PaLM 2",maxTokens:-1,tags:[],descriptions:[{label:"Description",value:"The most advanced model by Google. Powers Bard, PaLM API, MakerSuite, and various Workspace features at Google."},{label:"What it can do",value:"Reasoning, multilingual translation, coding, and more."}],uploadFileConfig:{maxFileSize:25*1024*1024,accept:".jpg,.jpeg,.png,.webp",acceptTooltip:"Upload file JEPEG, PNG, WEBP",maxCount:1}}];var y=[{title:"Gemini Nano",titleTag:"",value:"PaLM 2",maxTokens:-1,tags:[],descriptions:[{label:"Description",value:"The most advanced model by Google. Powers Gemini, PaLM API, MakerSuite, and various Workspace features at Google."},{label:"What it can do",value:"Reasoning, multilingual translation, coding, and more."}],uploadFileConfig:{maxFileSize:25*1024*1024,accept:".jpg,.jpeg,.png,.webp",acceptTooltip:"Upload file JEPEG, PNG, WEBP",maxCount:1}}];var o=(e,t=2)=>Number(e).toFixed(t).replace(/\B(?=(\d{3})+(?!\d))/g,",");var b=i(m());var _=[{title:"gpt-4",titleTag:"",value:"gpt-4",maxTokens:8192,tags:[],descriptions:[{label:"Max tokens",value:`${o(8192,0)} tokens`},{label:"Description",value:"More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat. Will be updated with OpenAI's latest model iteration 2 weeks after it is released."},{label:"Training date",value:`Up to ${(0,b.default)("2021-09-01").format("MMM YYYY")}`}]}];var w=[{title:"claude-2-100k",titleTag:"",value:"claude-2.0",maxTokens:100*1e3,tags:[],descriptions:[{label:"Max tokens",value:`${o(100*1e3,0)} tokens`},{label:"Description",value:"Superior performance on tasks that require complex reasoning. Claude 2 is Anthropic's best-in-class offering."}],uploadFileConfig:{accept:".pdf,.doc,.docx,.rtf,.epub,.odt,.odp,.pptx,.txt,.py,.ipynb,.js,.jsx,.html,.css,.java,.cs,.php,.c,.cpp,.cxx,.h,.hpp,.rs,.R,.Rmd,.swift,.go,.rb,.kt,.kts,.ts,.tsx,.m,.scala,.rs,.dart,.lua,.pl,.pm,.t,.sh,.bash,.zsh,.csv,.log,.ini,.config,.json,.yaml,.yml,.toml,.lua,.sql,.bat,.md,.coffee",acceptTooltip:"Add files (5 max, 10MB each). Accepts pdf, txt, csv, etc.",maxFileSize:10*1024*1024,maxCount:5}}];var a=i(T());var z=`You are a knowledgeable and helpful person that can answer any questions. Your task is to answer questions.

It's possible that the question, or just a portion of it, requires relevant information from the internet to give a satisfactory answer. The relevant search results provided below, delimited by <search_results></search_results>, are the necessary information already obtained from the internet. The search results set the context for addressing the question, so you don't need to access the internet to answer the question.

Write a comprehensive answer to the question in the best way you can. If necessary, use the provided search results.

Search results:
<search_results>
{web_results}
</search_results>

Each search result item provides the following information in this format:
Number: [Index number of the search result]
URL: [URL of the search result]
Title: [Page title of the search result]
Content: [Page content of the search result]

If you can't find enough information in the search results and you're not sure about the answer, try your best to give a helpful response by using all the information you have from the search results.

For your reference, today's date is {current_date}.

---

You should always respond using the following Markdown format delimited by:

# {query}

## \u{1F5D2}\uFE0F Answer
<answer to the question>

## \u{1F310} Sources
<numbered list of all the provided search results>

---

Here are more requirements for the response Markdown format described above:

For <answer to the question> part in the above Markdown format:
If you use any of the search results in <answer to the question>, always cite the sources at the end of the corresponding line, similar to how Wikipedia.org cites information. Use the citation format [[NUMBER](URL)], where both the NUMBER and URL correspond to the provided search results in <numbered list of all the provided search results>.

Present the answer in a clear format.
Use a numbered list if it clarifies things
Make the answer as short as possible, ideally no more than 200 words.

For <numbered list of all the provided search results> part in the above Markdown format:
Always list all the search results provided above, delimited by <search_results></search_results>.
Do not miss any search result items, regardless if there are duplicated ones in the provided search results.
Use the following format for each search result item:
[the domain of the URL - TITLE](URL)
Ensure the bullet point's number matches the 'NUMBER' of the corresponding search result item.`,$=`You are a knowledgeable and helpful person that can answer any questions. Your task is to answer questions.

It's possible that the question, or just a portion of it, requires relevant information from the internet to give a satisfactory answer. The relevant search results provided below, delimited by <search_results></search_results>, are the necessary information already obtained from the internet. The search results set the context for addressing the question, so you don't need to access the internet to answer the question.

Write a comprehensive answer to the question in the best way you can. If necessary, use the provided search results.

Search results:
<search_results>
{web_results}
</search_results>

Each search result item provides the following information in this format:
Number: [Index number of the search result]
URL: [URL of the search result]
Title: [Page title of the search result]
Content: [Page content of the search result]

If you can't find enough information in the search results and you're not sure about the answer, try your best to give a helpful response by using all the information you have from the search results.

For your reference, today's date is {current_date}.

---

You should always respond using the following Markdown format:

# {query}

## \u{1F5D2}\uFE0F Answer
<answer to the question>

## \u{1F310} Sources
<numbered list of all the provided search results>

---

Here are more requirements for the response Markdown format described above:

For <answer to the question> part in the above Markdown format:
If you use any of the search results in <answer to the question>, always cite the sources at the end of the corresponding line, similar to how Wikipedia.org cites information. Use the citation format [[NUMBER](URL)], where both the NUMBER and URL correspond to the provided search results in <numbered list of all the provided search results>.

Present the answer in a clear format.
Use a numbered list if it clarifies things
Make the answer as short as possible, ideally no more than 200 words.

For <numbered list of all the provided search results> part in the above Markdown format:
Always list all the search results provided above, delimited by <search_results></search_results>.
Do not miss any search result items, regardless if there are duplicated ones in the provided search results.
Use the following format for each search result item:
[the domain of the URL - TITLE](URL)
Ensure the bullet point's number matches the 'NUMBER' of the corresponding search result item.`,J=`You are a knowledgeable and helpful person that can answer any questions. Your task is to answer questions.

It's possible that the question, or just a portion of it, requires relevant information from the internet to give a satisfactory answer. The relevant search results provided below, delimited by <search_results></search_results>, are the necessary information already obtained from the internet. The search results set the context for addressing the question, so you don't need to access the internet to answer the question.

Write a comprehensive answer to the question in the best way you can. If necessary, use the provided search results.

Search results:
<search_results>
{web_results}
</search_results>

Each search result item provides the following information in this format:
Number: [Index number of the search result]
URL: [URL of the search result]
Title: [Page title of the search result]
Content: [Page content of the search result]

If you can't find enough information in the search results and you're not sure about the answer, try your best to give a helpful response by using all the information you have from the search results.

For your reference, today's date is {current_date}.

---

You should always respond using the following Markdown format delimited by:

# {query}

## \u{1F5D2}\uFE0F Answer
<answer to the question>

## \u{1F310} Sources
<numbered list of all the provided search results>

---

Here are more requirements for the response Markdown format described above:

For <answer to the question> part in the above Markdown format:
If you use any of the search results in <answer to the question>, always cite the sources at the end of the corresponding line, similar to how Wikipedia.org cites information. Use the citation format [[NUMBER](URL)], where both the NUMBER and URL correspond to the provided search results in <numbered list of all the provided search results>.

Present the answer in a clear format.
Use a numbered list if it clarifies things
Make the answer as short as possible, ideally no more than 200 words.

For <numbered list of all the provided search results> part in the above Markdown format:
Always list all the search results provided above, delimited by <search_results></search_results>.
Do not miss any search result items, regardless if there are duplicated ones in the provided search results.
Use the following format for each search result item:
[the domain of the URL - TITLE](URL)
Ensure the bullet point's number matches the 'NUMBER' of the corresponding search result item.`,I=`You are a knowledgeable and helpful person that can answer any questions. Your task is to answer questions.

It's possible that the question, or just a portion of it, requires relevant information from the internet to give a satisfactory answer. The relevant search results provided below, delimited by <search_results></search_results>, are the necessary information already obtained from the internet. The search results set the context for addressing the question, so you don't need to access the internet to answer the question.

Write a comprehensive answer to the question in the best way you can. If necessary, use the provided search results.

Search results:
<search_results>
{web_results}
</search_results>

Each search result item provides the following information in this format:
Number: [Index number of the search result]
URL: [URL of the search result]
Title: [Page title of the search result]
Content: [Page content of the search result]

If you can't find enough information in the search results and you're not sure about the answer, try your best to give a helpful response by using all the information you have from the search results.

For your reference, today's date is {current_date}.

---

You should always respond using the following Markdown format delimited by:

# {query}

## \u{1F5D2}\uFE0F Answer
<answer to the question>

## \u{1F310} Sources
<numbered list of all the provided search results>

---

Here are more requirements for the response Markdown format described above:

For <answer to the question> part in the above Markdown format:
If you use any of the search results in <answer to the question>, always cite the sources at the end of the corresponding line, similar to how Wikipedia.org cites information. Use the citation format [[NUMBER](URL)], where both the NUMBER and URL correspond to the provided search results in <numbered list of all the provided search results>.

Present the answer in a clear format.
Use a numbered list if it clarifies things
Make the answer as short as possible, ideally no more than 200 words.

For <numbered list of all the provided search results> part in the above Markdown format:
Always list all the search results provided above, delimited by <search_results></search_results>.
Do not miss any search result items, regardless if there are duplicated ones in the provided search results.
Use the following format for each search result item:
[the domain of the URL - TITLE](URL)
Ensure the bullet point's number matches the 'NUMBER' of the corresponding search result item.`,Q=I;var S=i(m()),M=`You are a research expert who is good at coming up with the perfect search query to help find answers to any question. Your task is to think of the most effective search query for the following question delimited by <question></question>:

<question>
{{current_question}}
</question>

The question is the final one in a series of previous questions and answers. Here are the earlier questions listed in the order they were asked, from the very first to the one before the final question, delimited by <previous_questions></previous_questions>:
<previous_questions>
{{previous_questions}}
</previous_questions>

For your reference, today's date is {{CURRENT_DATE}}.

Output 3 search queries as JSON Array format without additional number, context, explanation, or extra wording, site information, just 3 text search queries as JSON Array format.`,A=`You are a research expert who is good at coming up with the perfect search query to help find answers to any question. Your task is to think of the most effective search query for the following question delimited by <question></question>:

<question>
{{current_question}}
</question>

The question is the final one in a series of previous questions and answers. Here are the earlier questions listed in the order they were asked, from the very first to the one before the final question, delimited by <previous_questions></previous_questions>:
<previous_questions>
{{previous_questions}}
</previous_questions>

For your reference, today's date is {{CURRENT_DATE}}.

Output 1 search query as JSON Array format without additional number, context, explanation, or extra wording, site information, just 1 text search query as JSON Array format.`,P=`You are a research expert specializing in crafting optimal search queries to find answers to questions with context. Your task is to generate effective search queries based on the current question and previous questions.

First, review the previous questions:
<previous_questions>
{{previous_questions}}
</previous_questions>

Now, consider the current question and today's date:
<current_question>
{{current_question}}
</current_question>

Today's date: {{CURRENT_DATE}}

Your objective is to create 4 effective search queries for the current question, learning from the context provided by the previous questions.

Follow these steps:
1. Add the current question as the first search query.
2. Analyze the current question and the previous questions to understand the context and potential search patterns.
3. Rewrite the current question into a effective concise search query, incorporating relevant context from previous questions if applicable.
4. Repeat step 3 to generate a total of 3 more unique, concise and effective search queries.
5. Format the search queries as a valid JSON array.
 

Output your response in the following JSON format, without any additional commentary:
[current_question,"query 2",...,"query 4"]

Remember to focus solely on generating the search queries. Do not provide any explanations or additional text outside of the JSON array.`,U=`You are a research expert specializing in crafting optimal search queries to find answers to questions with context. Your task is to generate effective search queries based on the current question.

Consider the current question and today's date:
<current_question>
{{current_question}}
</current_question>

Today's date: {{CURRENT_DATE}}

Your objective is to create 4 effective search queries for the current question, learning from the context provided by the previous questions.

Follow these steps:
1. Add the current question as the first search query.
2. Analyze the current question and the previous questions to understand the context and potential search patterns.
3. Rewrite the current question into a effective concise search query, incorporating relevant context from previous questions if applicable.
4. Repeat step 3 to generate a total of 3 more unique, concise and effective search queries.
5. Format the search queries as a valid JSON array.
 

Output your response in the following JSON format, without any additional commentary:
[current_question,"query 2",...,"query 4"]

Remember to focus solely on generating the search queries. Do not provide any explanations or additional text outside of the JSON array.`,V=",",K=3,X=4,C={single:A,multiple:M,strengthen_no_history:U,strengthen_have_history:P},ee=(e,t="single")=>{let n=t;t==="chatgpt_strengthen"&&(e.length>1?n="strengthen_have_history":n="strengthen_no_history");let s=C[n];s=s.replaceAll("{{CURRENT_DATE}}",(0,S.default)().format("YYYY-MM-DD HH:mm:ss"));let R=e[e.length-1],u=e.slice(0,-1);s=s.replaceAll("{{current_question}}",R);let c="";return u.forEach((x,h)=>{c+=`${h+1}) ${x}${h<u.length-1?`
`:""}`}),s=s.replaceAll("{{previous_questions}}",c),s};var re=[{value:"sogou",label:"Sogou Search"},{value:"brave",label:"Brave Search"},{value:"yandex",label:"Yandex Search"},{value:"naver",label:"Naver Search"},{value:"bing",label:"Bing Search"},{value:"yahoo",label:"Yahoo Search"},{value:"baidu",label:"Baidu Search"},{value:"google",label:"Google Search"}],q=Array.from({length:10},(e,t)=>t+1).map(e=>({value:e,label:`${e} result${e===1?"":"s"}`}));q.push({value:15,label:"Max results"});var se=q,N="NO_SUMMARIZE",oe=[{value:"MAP_REDUCE",label:"Pro search"},{value:N,label:"Quick search"}],ae=[{value:"m",label:"Past month"},{value:"w",label:"Past week"},{value:"d",label:"Past day"},{value:"any",label:"Any time"}],l="IN_DEPTH",O="BRIEF",ne=[{value:l,label:"Comprehensive"},{value:O,label:"Concise"}];var E={loaded:!1,language:"en",numWebResults:6,webAccess:!0,webAccessDisabled:!1,isHaveChatgptSearchButton:!1,chatgptWebAccess:null,chatgptNumWebResults:10,isWebAccessPassivelyClosed:!1,region:"wt-wt",timePeriod:"any",aiResponseLanguage:"auto",promptUUID:"default",searchEngine:"google",trimLongText:!1,summarizeType:"NO_SUMMARIZE",chatgptSummarizeType:l,promptLibrary:!0,colorSchema:"auto",conversationId:"",currentProvider:r.OPENAI,currentModel:"",thirdProviderSettings:{[r.BING]:{conversationStyle:"balanced",model:_[0].value},[r.CLAUDE]:{model:w[0].value},[r.BARD]:{model:v[0].value},[r.OPENAI]:{model:p},[r.FREE_AI]:{model:g[0].value},[r.GEMINI]:{model:y[0].value}}};async function k(){let e=await a.default.storage.sync.get(E);return f(e,E)}async function L(e){await a.default.storage.sync.set(e)}async function _e(e){try{if(e instanceof Function){let t=await k();await a.default.storage.sync.set(e(t))}else await L(e);return!0}catch(t){return!1}}function we(){window.dispatchEvent(new CustomEvent(d,{}))}export{g as a,z as b,$ as c,J as d,I as e,Q as f,V as g,K as h,X as i,ee as j,re as k,se as l,oe as m,ae as n,l as o,O as p,ne as q,E as r,k as s,L as t,_e as u,we as v};
