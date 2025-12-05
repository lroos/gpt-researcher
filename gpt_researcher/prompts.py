import warnings
from datetime import date, datetime, timezone

from langchain_core.documents import Document

from .config import Config
from .utils.enum import ReportSource, ReportType, Tone
from .utils.enum import PromptFamily as PromptFamilyEnum
from typing import Callable, List, Dict, Any


## Prompt Families #############################################################

class PromptFamily:
    """General purpose class for prompt formatting.

    This may be overwritten with a derived class that is model specific. The
    methods are broken down into two groups:

    1. Prompt Generators: These follow a standard format and are correlated with
        the ReportType enum. They should be accessed via
        get_prompt_by_report_type

    2. Prompt Methods: These are situation-specific methods that do not have a
        standard signature and are accessed directly in the agent code.

    All derived classes must retain the same set of method names, but may
    override individual methods.
    """

    def __init__(self, config: Config):
        """Initialize with a config instance. This may be used by derived
        classes to select the correct prompting based on configured models and/
        or providers
        """
        self.cfg = config

    # MCP-specific prompts
    @staticmethod
    def generate_mcp_tool_selection_prompt(query: str, tools_info: List[Dict], max_tools: int = 3) -> str:
        """
        Generate prompt for LLM-based MCP tool selection.
        
        Args:
            query: The research query
            tools_info: List of available tools with their metadata
            max_tools: Maximum number of tools to select
            
        Returns:
            str: The tool selection prompt
        """
        import json
        
        return f"""You are a research assistant helping to select the most relevant tools for a research query.

RESEARCH QUERY: "{query}"

AVAILABLE TOOLS:
{json.dumps(tools_info, indent=2)}

TASK: Analyze the tools and select EXACTLY {max_tools} tools that are most relevant for researching the given query.

SELECTION CRITERIA:
- Choose tools that can provide information, data, or insights related to the query
- Prioritize tools that can search, retrieve, or access relevant content
- Consider tools that complement each other (e.g., different data sources)
- Exclude tools that are clearly unrelated to the research topic

Return a JSON object with this exact format:
{{
  "selected_tools": [
    {{
      "index": 0,
      "name": "tool_name",
      "relevance_score": 9,
      "reason": "Detailed explanation of why this tool is relevant"
    }}
  ],
  "selection_reasoning": "Overall explanation of the selection strategy"
}}

Select exactly {max_tools} tools, ranked by relevance to the research query.
"""

    @staticmethod
    def generate_mcp_research_prompt(query: str, selected_tools: List) -> str:
        """
        Generate prompt for MCP research execution with selected tools.
        
        Args:
            query: The research query
            selected_tools: List of selected MCP tools
            
        Returns:
            str: The research execution prompt
        """
        # Handle cases where selected_tools might be strings or objects with .name attribute
        tool_names = []
        for tool in selected_tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            else:
                tool_names.append(str(tool))
        
        return f"""You are a research assistant with access to specialized tools. Your task is to research the following query and provide comprehensive, accurate information.

RESEARCH QUERY: "{query}"

INSTRUCTIONS:
1. Use the available tools to gather relevant information about the query
2. Call multiple tools if needed to get comprehensive coverage
3. If a tool call fails or returns empty results, try alternative approaches
4. Synthesize information from multiple sources when possible
5. Focus on factual, relevant information that directly addresses the query

AVAILABLE TOOLS: {tool_names}

Please conduct thorough research and provide your findings. Use the tools strategically to gather the most relevant and comprehensive information."""

    @staticmethod
    def generate_search_queries_prompt(
        question: str,
        parent_query: str,
        report_type: str,
        max_iterations: int = 3,
        context: List[Dict[str, Any]] = [],
    ):
        """Generates the search queries prompt for the given question.
        Args:
            question (str): The question to generate the search queries prompt for
            parent_query (str): The main question (only relevant for detailed reports)
            report_type (str): The report type
            max_iterations (int): The maximum number of search queries to generate
            context (str): Context for better understanding of the task with realtime web information

        Returns: str: The search queries prompt for the given question
        """

        if (
            report_type == ReportType.DetailedReport.value
            or report_type == ReportType.SubtopicReport.value
        ):
            task = f"{parent_query} - {question}"
        else:
            task = question

        context_prompt = f"""
You are a specialized retail real estate acquisitions research assistant. Your task is to generate comprehensive search queries for: "{task}".

The query should specify a tenant/store name and an address/city/state. Parse this information and generate search queries that cover ALL critical dimensions for acquisition analysis:

Context: {context}

Use this context to inform and refine your search queries. The context provides real-time web information that can help you generate more specific and relevant queries. Consider any current events, recent developments, or specific details mentioned in the context that could enhance the search queries.
""" if context else f"""
You are a specialized retail real estate acquisitions research assistant generating search queries for: "{task}".

The query should specify a tenant/store name and an address/city/state. Parse this information and create queries covering ALL dimensions.
"""

        dynamic_example = ", ".join([f'"query {i+1}"' for i in range(max_iterations)])

        return f"""Generate {max_iterations} strategic search queries for retail real estate acquisition due diligence on: "{task}"

{context_prompt}

CRITICAL: Parse the tenant/store name and location (address/city/state) from the query, then generate searches covering these dimensions:
1. TENANT SCREENING: Credit ratings, brand strength, financial performance, store openings/closures, expansion/contraction plans, lease renewal rates, CEO changes, restructuring
2. LEASE ANALYSIS: Lease structure (NNN, FSG, Modified Gross), lease terms, rent roll, escalation clauses, expense pass-throughs
3. LOCATION QUALITY: Demographics, household income, retail demand drivers, foot traffic, walkability scores, livability scores, crime rates
4. MARKET BENCHMARK: Lease comps, cap rates, occupancy rates, market lease rates, cap rate trends
5. ASSET QUALITY: Building class (A/B/C), age and condition, ESG certifications (LEED, WELL, GRESB)
6. ECONOMIC ANALYSIS: Local employment, economic indicators, business activity, consumer spending patterns
7. COMPETITIVE LANDSCAPE: Nearby competitors, market saturation, similar retailers in area
8. DEVELOPMENT ACTIVITY: New construction, zoning changes, multifamily projects, grand openings, residential development permits
9. MACRO TRENDS: Interest rates, cap rate trends, retail sector health, consumer behavior trends

Example Search Query Patterns:
- "[tenant name] credit rating [current year]"
- "[tenant name] lease renewal rate investment grade"
- "[tenant name] NNN lease structure expansion"
- "[tenant name] store closures CEO change financial performance"
- "[property address] walkability score crime rate"
- "[city/neighborhood name] demographics household income livability"
- "[city/neighborhood name] retail lease comps cap rates [current year]"
- "[city/neighborhood name] new residential development multifamily breaking ground"
- "[city/neighborhood name] economic indicators employment consumer spending"
- "[retail sector] trends consumer behavior [current year]"
- "[tenant category] competitors [city/neighborhood]"
- "[property address] ESG certification LEED WELL GRESB"
- "[city/state] cap rate trends interest rates [current year]"
- "[city/neighborhood name] zoning changes infrastructure improvements"

Real Acquisition Manager Search Examples (from institutional net lease REIT methodology):
- "Kroger credit rating delivery centers closure investment grade"
- "CarMax CEO change financial performance lease renewal"
- "PNC Bank branch expansion strategy NNN lease"
- "Publix growth strategy Florida demographics household penetration"
- "[city name] new multifamily development breaking ground permits"
- "[neighborhood name] residential development demographics income trends"
- "[property address] Boulder Group net lease cap rates"
- "[tenant name] Numerator consumer trends brand performance"
- "[property address] IPA Commercial lease rates market comps"
- "[property address] GRESB ESG certification walkability"

NOTE: Replace placeholders like [tenant name], [property address], [city name], [neighborhood name], [retail sector], [tenant category] with actual parsed values from the research query.

Assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.

You MUST respond with a list of strings in the following format: [{dynamic_example}].
The response should contain ONLY the list of search query strings, nothing else.
"""

    @staticmethod
    def generate_report_prompt(
        question: str,
        context,
        report_source: str,
        report_format="apa",
        total_words=1000,
        tone=None,
        language="english",
    ):
        """Generates the report prompt for the given question and research summary.
        Args: question (str): The question to generate the report prompt for
                research_summary (str): The research summary to generate the report prompt for
        Returns: str: The report prompt for the given question and research summary
        """

        reference_prompt = ""
        if report_source == ReportSource.Web.value:
            reference_prompt = f"""
You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
Every url should be hyperlinked: [url website](url)
Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report:

eg: Author, A. A. (Year, Month Date). Title of web page. Website Name. [url website](url)
"""
        else:
            reference_prompt = f"""
You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."
"""

        tone_prompt = f"Write the report in a {tone.value} tone." if tone else ""

        return f"""
Information: "{context}"
---
You are a senior retail real estate acquisitions analyst following the rigorous methodology of a net lease REIT acquisition manager. Using the above information, generate a comprehensive acquisition due diligence report for: "{question}"

The report should provide a thorough analysis for evaluating this retail location acquisition opportunity. It must be well-structured, data-driven, and comprehensive, with at least {total_words} words.

REQUIRED REPORT STRUCTURE - Organize findings into these key sections:

## Executive Summary
Brief overview of the tenant, location, asset quality, and acquisition recommendation with key highlights

## Tenant Analysis
- Company financial health and credit ratings (investment grade preferred)
- Brand strength and consumer trends (top-performing brands, household penetration)
- Recent corporate developments (CEO changes, restructuring, expansions/closures)
- Store performance and growth strategy
- Lease renewal rates and tenant stability indicators
- Historical performance and growth trajectory

## Location Quality and Market Analysis (CRITICAL - Highest Priority)
- Detailed demographics: population, household income, age distribution
- Walkability and livability scores (community engagement factors)
- Crime rates and neighborhood safety
- Retail demand drivers: foot traffic, nearby anchors, accessibility
- Market lease rates and comparisons (cite IPA Commercial, Boulder Group when available)
- Cap rate trends and market context (note recent movements)
- Competitive positioning: visibility, accessibility, parking
- Residential development activity: new multifamily projects, breaking ground, permits
- Neighborhood characteristics and quality indicators
- Population growth trends and projections

## Lease Structure and Terms
- Lease type: NNN (Net Lease), FSG (Full Service Gross), or Modified Gross
- Lease duration and renewal options
- Rent escalations and terms
- Expense pass-throughs
- Below-market rent potential for upside
- Comparison to market lease comps

## Asset Quality and ESG Considerations
- Building class (A, B, or C)
- Age and condition of the property
- Physical obsolescence or recent renovations
- ESG certifications: LEED, WELL, or GRESB ratings
- Energy efficiency and sustainability features
- ESG lease clauses (energy, water, waste management)
- Long-term asset value enhancement potential

## Economic Analysis
- Local employment indicators and job market
- Economic health of the area
- Business activity and commercial development
- Consumer spending patterns by income segment (high-income vs. low-income households)

## Competitive Landscape
- Nearby competitors in the same retail category
- Market saturation analysis
- Competitive advantages/disadvantages of the location
- Similar tenants in the area

## Sector & Industry Trends
- Retail sector performance and trends (cite Numerator, industry publications when available)
- Category-specific dynamics
- Consumer behavior trends (experiential, community-based retail)
- Industry challenges and opportunities
- Relevant sector news affecting the tenant type

## Development & Zoning
- New construction and development projects
- Zoning changes or planning updates
- Infrastructure improvements
- Grand openings of complementary businesses

## Macro-Economic and Market Risk Assessment
- Interest rate environment and cap rate impacts
- Federal Reserve policy trends
- Consumer sentiment and retail sector health
- High-income vs. low-income segment performance
- Supply/demand balance in the market

## Risk Assessment
- Key risks identified from the research
- Mitigation strategies
- Red flags or concerns
- Demographic and economic headwinds

## Scoring and Investment Analysis
Present a weighted scoring breakdown (use table format):
- Tenant credit and performance (30% weight)
- Location quality and market dynamics (30% weight)
- Asset quality and ESG compliance (20% weight)
- Lease structure and terms (10% weight)
- Macro-economic risk (10% weight)

## Acquisition Recommendation
- Clear recommendation (proceed/reconsider/decline)
- Key supporting factors based on scoring
- Projected returns and alignment with portfolio strategy
- Conditions or caveats
- Risk mitigation strategies for proceeding

Please follow all of the following guidelines:
- You MUST determine a concrete acquisition recommendation based on the data. Do NOT provide vague conclusions.
- You MUST write the report with markdown syntax and {report_format} format.
- Structure your report with clear markdown headers: use # for the main title, ## for major sections, and ### for subsections.
- Use markdown tables when presenting structured data, demographics, comparisons, or scoring to enhance readability.
- PRIORITIZE location quality (demographics, walkability, development activity) and tenant creditworthiness - these are critical for acquisition decisions.
- You MUST prioritize the relevance, reliability, and significance of the sources. Trusted sources include: Boulder Group, IPA Commercial, GRESB, Numerator, SEC filings, credit rating agencies.
- Prioritize recent articles and data from the past 12 months when available.
- You MUST NOT include a table of contents, but DO include proper markdown headers (# ## ###).
- Use in-text citation references in {report_format} format with markdown hyperlinks: ([in-text citation](url)).
- Include specific data points, numbers, statistics, and dates whenever available.
- Don't forget to add a reference list at the end of the report in {report_format} format.
- {reference_prompt}
- {tone_prompt}

You MUST write the report in the following language: {language}.
This acquisition analysis is critical for investment decisions and follows best practices for net lease retail real estate due diligence.
Assume that the current date is {date.today()}.
"""

    @staticmethod
    def curate_sources(query, sources, max_results=10):
        return f"""Your goal is to evaluate and curate the provided scraped content for the research task: "{query}"
    while prioritizing the inclusion of relevant and high-quality information, especially sources containing statistics, numbers, or concrete data.

The final curated list will be used as context for creating a research report, so prioritize:
- Retaining as much original information as possible, with extra emphasis on sources featuring quantitative data or unique insights
- Including a wide range of perspectives and insights
- Filtering out only clearly irrelevant or unusable content

EVALUATION GUIDELINES:
1. Assess each source based on:
   - Relevance: Include sources directly or partially connected to the research query. Err on the side of inclusion.
   - Credibility: Favor authoritative sources but retain others unless clearly untrustworthy.
   - Currency: Prefer recent information unless older data is essential or valuable.
   - Objectivity: Retain sources with bias if they provide a unique or complementary perspective.
   - Quantitative Value: Give higher priority to sources with statistics, numbers, or other concrete data.
2. Source Selection:
   - Include as many relevant sources as possible, up to {max_results}, focusing on broad coverage and diversity.
   - Prioritize sources with statistics, numerical data, or verifiable facts.
   - Overlapping content is acceptable if it adds depth, especially when data is involved.
   - Exclude sources only if they are entirely irrelevant, severely outdated, or unusable due to poor content quality.
3. Content Retention:
   - DO NOT rewrite, summarize, or condense any source content.
   - Retain all usable information, cleaning up only clear garbage or formatting issues.
   - Keep marginally relevant or incomplete sources if they contain valuable data or insights.

SOURCES LIST TO EVALUATE:
{sources}

You MUST return your response in the EXACT sources JSON list format as the original sources.
The response MUST not contain any markdown format or additional text (like ```json), just the JSON list!
"""

    @staticmethod
    def generate_resource_report_prompt(
        question, context, report_source: str, report_format="apa", tone=None, total_words=1000, language="english"
    ):
        """Generates the resource report prompt for the given question and research summary.

        Args:
            question (str): The question to generate the resource report prompt for.
            context (str): The research summary to generate the resource report prompt for.

        Returns:
            str: The resource report prompt for the given question and research summary.
        """

        reference_prompt = ""
        if report_source == ReportSource.Web.value:
            reference_prompt = f"""
            You MUST include all relevant source urls.
            Every url should be hyperlinked: [url website](url)
            """
        else:
            reference_prompt = f"""
            You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."
        """

        return (
            f'"""{context}"""\n\nBased on the above information, generate a bibliography recommendation report for the following'
            f' question or topic: "{question}". The report should provide a detailed analysis of each recommended resource,'
            " explaining how each source can contribute to finding answers to the research question.\n"
            "Focus on the relevance, reliability, and significance of each source.\n"
            "Ensure that the report is well-structured, informative, in-depth, and follows Markdown syntax.\n"
            "Use markdown tables and other formatting features when appropriate to organize and present information clearly.\n"
            "Include relevant facts, figures, and numbers whenever available.\n"
            f"The report should have a minimum length of {total_words} words.\n"
            f"You MUST write the report in the following language: {language}.\n"
            "You MUST include all relevant source urls."
            "Every url should be hyperlinked: [url website](url)"
            f"{reference_prompt}"
        )

    @staticmethod
    def generate_custom_report_prompt(
        query_prompt, context, report_source: str, report_format="apa", tone=None, total_words=1000, language: str = "english"
    ):
        return f'"{context}"\n\n{query_prompt}'

    @staticmethod
    def generate_outline_report_prompt(
        question, context, report_source: str, report_format="apa", tone=None,  total_words=1000, language: str = "english"
    ):
        """Generates the outline report prompt for the given question and research summary.
        Args: question (str): The question to generate the outline report prompt for
                research_summary (str): The research summary to generate the outline report prompt for
        Returns: str: The outline report prompt for the given question and research summary
        """

        return (
            f'"""{context}""" Using the above information, generate an outline for a research report in Markdown syntax'
            f' for the following question or topic: "{question}". The outline should provide a well-structured framework'
            " for the research report, including the main sections, subsections, and key points to be covered."
            f" The research report should be detailed, informative, in-depth, and a minimum of {total_words} words."
            " Use appropriate Markdown syntax to format the outline and ensure readability."
            " Consider using markdown tables and other formatting features where they would enhance the presentation of information."
        )

    @staticmethod
    def generate_deep_research_prompt(
        question: str,
        context: str,
        report_source: str,
        report_format="apa",
        tone=None,
        total_words=2000,
        language: str = "english"
    ):
        """Generates the deep research report prompt, specialized for handling hierarchical research results.
        Args:
            question (str): The research question
            context (str): The research context containing learnings with citations
            report_source (str): Source of the research (web, etc.)
            report_format (str): Report formatting style
            tone: The tone to use in writing
            total_words (int): Minimum word count
            language (str): Output language
        Returns:
            str: The deep research report prompt
        """
        reference_prompt = ""
        if report_source == ReportSource.Web.value:
            reference_prompt = f"""
You MUST write all used source urls at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each.
Every url should be hyperlinked: [url website](url)
Additionally, you MUST include hyperlinks to the relevant URLs wherever they are referenced in the report:

eg: Author, A. A. (Year, Month Date). Title of web page. Website Name. [url website](url)
"""
        else:
            reference_prompt = f"""
You MUST write all used source document names at the end of the report as references, and make sure to not add duplicated sources, but only one reference for each."
"""

        tone_prompt = f"Write the report in a {tone.value} tone." if tone else ""

        return f"""
Using the following hierarchically researched information and citations:

"{context}"

Write a comprehensive research report answering the query: "{question}"

The report should:
1. Synthesize information from multiple levels of research depth
2. Integrate findings from various research branches
3. Present a coherent narrative that builds from foundational to advanced insights
4. Maintain proper citation of sources throughout
5. Be well-structured with clear sections and subsections
6. Have a minimum length of {total_words} words
7. Follow {report_format} format with markdown syntax
8. Use markdown tables, lists and other formatting features when presenting comparative data, statistics, or structured information

Additional requirements:
- Prioritize insights that emerged from deeper levels of research
- Highlight connections between different research branches
- Include relevant statistics, data, and concrete examples
- You MUST determine your own concrete and valid opinion based on the given information. Do NOT defer to general and meaningless conclusions.
- You MUST prioritize the relevance, reliability, and significance of the sources you use. Choose trusted sources over less reliable ones.
- You must also prioritize new articles over older articles if the source can be trusted.
- Use in-text citation references in {report_format} format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).
- {tone_prompt}
- Write in {language}

{reference_prompt}

Please write a thorough, well-researched report that synthesizes all the gathered information into a cohesive whole.
Assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')}.
"""

    @staticmethod
    def auto_agent_instructions():
        return """
This task involves researching retail tenant locations for real estate acquisition analysis following a high-fidelity, institutional-grade methodology. The research query will always specify a tenant/store name and an address/city/state. Your role is to conduct comprehensive due diligence research as a senior retail real estate acquisitions analyst at a net lease REIT.

Agent
You are a 🏢 Senior Retail Real Estate Acquisitions Agent - a specialized research assistant following the rigorous methodology used by top-performing net lease REITs to evaluate retail tenant locations for acquisition opportunities.

Your agent role prompt should be:
{
    "server": "🏢 Senior Retail Real Estate Acquisitions Agent",
    "agent_role_prompt": "You are an expert senior retail real estate acquisitions analyst AI assistant modeled after acquisition managers at leading net lease REITs. Your goal is to conduct institutional-grade due diligence on retail tenant locations. You systematically analyze: tenant creditworthiness and brand strength; location quality (demographics, walkability, crime rates); asset quality and ESG credentials; lease structures and terms; market rates and cap trends; competitive landscape; and macro-economic factors. You synthesize data into structured scoring models and provide detailed reports with concrete acquisition recommendations evaluating investment viability and risk."
}

Automated Research Workflow (Step-by-Step):
1. TENANT SCREENING: Scrape news, SEC filings, earnings reports for tenant financials, credit ratings, expansion/contraction plans, lease renewal rates, brand strength
2. LEASE ANALYSIS: Extract lease structure (NNN, FSG, Modified Gross), terms, rent roll, escalation clauses, expense pass-throughs
3. MARKET BENCHMARK: Pull lease comps, cap rates, occupancy rates in the submarket from IPA Commercial, Boulder Group, CoStar
4. DEMOGRAPHIC SCAN: Analyze census data, income levels, retail demand data, walkability scores, crime rates for the trade area
5. ESG & ASSET REVIEW: Check for LEED, WELL, GRESB certifications; assess building class, age, condition, energy efficiency
6. ECONOMIC ANALYSIS: Monitor local employment, consumer spending patterns, business activity
7. COMPETITIVE LANDSCAPE: Identify nearby competitors, assess market saturation
8. DEVELOPMENT ACTIVITY: Track new construction, zoning changes, multifamily projects, infrastructure improvements
9. MACRO TRENDS: Monitor interest rates, cap rate trends, consumer behavior trends, retail sector health from Boulder Group, Numerator, Fed releases
10. SYNTHESIS & SCORING: Aggregate findings into weighted scoring model (Tenant 30%, Location 30%, Asset 20%, Lease 10%, Macro 10%)

Research Focus Areas (Critical Dimensions):
- Tenant/Company Analysis: Credit ratings (investment grade preferred), financial health, brand strength, household penetration, CEO changes, restructuring, store openings/closures, lease renewal rates
- Location Quality: Demographics, household income, age distribution, walkability scores, livability scores, crime rates, foot traffic, nearby anchors, accessibility
- Market Benchmark: Lease comps, cap rates, cap rate trends, market lease rates, occupancy rates
- Lease Structure: NNN vs. FSG vs. Modified Gross, lease duration, renewal options, rent escalations, expense pass-throughs, below-market rent potential
- Asset Quality: Building class (A/B/C), age and condition, renovations, physical obsolescence
- ESG Considerations: LEED, WELL, GRESB certifications, energy efficiency, ESG lease clauses, sustainability features
- Neighborhood Analysis: Residential development, multifamily projects, population growth, permits, neighborhood characteristics
- Economic Analysis: Employment rates, economic indicators, local business activity, consumer spending by income segment
- Competitive Analysis: Nearby competitors, market saturation, similar retailers in area, competitive positioning
- Development Activity: New construction, zoning changes, infrastructure improvements, grand openings
- Sector Trends: Industry-specific news, retail category performance, consumer behavior trends (experiential, community-based)
- Macro Trends: Interest rates, Federal Reserve policy, consumer sentiment, supply/demand balance

Key Trusted Information Sources (Prioritize These):
- Boulder Group: Net lease cap rate trends, market reports
- IPA Commercial: Commercial real estate lease rates, market comps
- GRESB: ESG certifications, walkability scores, livability metrics
- Numerator: Consumer trends, brand performance, household penetration
- SEC: Tenant financials, 10-K/10-Q filings, earnings reports
- Credit rating agencies: Moody's, S&P, Fitch ratings
- Census.gov: Demographics, population data
- Local economic development agencies: Area economic indicators
- Industry publications: RetailDive, CStoreDive, GroceryDive, National Real Estate Investor
- Real estate analytics: CoStar (when available), offering memoranda
- Zoning and planning department records
- Company press releases and announcements

Analytical Methods to Apply:
- Time-series analysis: Track rent and cap rate trends over time
- Peer benchmarking: Compare tenant and asset to industry peers
- Sentiment analysis: Analyze news and earnings call transcripts
- ESG compliance scoring: Rate certifications and sustainability features
- Weighted scoring model: 30% tenant, 30% location, 20% asset, 10% lease, 10% macro

Source Prioritization:
- Prefer reports and data from the past 12 months for recency
- Prioritize established, reliable sources (Boulder Group, IPA Commercial, GRESB, Numerator, SEC)
- Verify data across multiple sources when possible
- Weight quantitative data and statistics heavily

Strategic Imperatives (Acquisition Criteria):
- Anchor assets with top-performing, creditworthy tenants (investment grade) in growth sectors
- Prioritize locations with strong demographic tailwinds, high walkability, community engagement
- Secure assets with robust ESG credentials and favorable lease structures (NNN, long term, escalations)
- Monitor macro-economic shifts (interest rates, consumer sentiment) to adjust underwriting
- Seek below-market rents for upside potential
- Focus on markets with positive demographic and economic trends
"""

    @staticmethod
    def generate_summary_prompt(query, data):
        """Generates the summary prompt for the given question and text.
        Args: question (str): The question to generate the summary prompt for
                text (str): The text to generate the summary prompt for
        Returns: str: The summary prompt for the given question and text
        """

        return (
            f'{data}\n Using the above text, summarize it based on the following task or query: "{query}".\n If the '
            f"query cannot be answered using the text, YOU MUST summarize the text in short.\n Include all factual "
            f"information such as numbers, stats, quotes, etc if available. "
        )

    @staticmethod
    def pretty_print_docs(docs: list[Document], top_n: int | None = None) -> str:
        """Compress the list of documents into a context string"""
        return f"\n".join(f"Source: {d.metadata.get('source')}\n"
                          f"Title: {d.metadata.get('title')}\n"
                          f"Content: {d.page_content}\n"
                          for i, d in enumerate(docs)
                          if top_n is None or i < top_n)

    @staticmethod
    def join_local_web_documents(docs_context: str, web_context: str) -> str:
        """Joins local web documents with context scraped from the internet"""
        return f"Context from local documents: {docs_context}\n\nContext from web sources: {web_context}"

    ################################################################################################

    # DETAILED REPORT PROMPTS

    @staticmethod
    def generate_subtopics_prompt() -> str:
        return """
Provided the main topic:

{task}

and research data:

{data}

- Construct a list of subtopics which indicate the headers of a report document to be generated on the task.
- These are a possible list of subtopics : {subtopics}.
- There should NOT be any duplicate subtopics.
- Limit the number of subtopics to a maximum of {max_subtopics}
- Finally order the subtopics by their tasks, in a relevant and meaningful order which is presentable in a detailed report

"IMPORTANT!":
- Every subtopic MUST be relevant to the main topic and provided research data ONLY!

{format_instructions}
"""

    @staticmethod
    def generate_subtopic_report_prompt(
        current_subtopic,
        existing_headers: list,
        relevant_written_contents: list,
        main_topic: str,
        context,
        report_format: str = "apa",
        max_subsections=5,
        total_words=800,
        tone: Tone = Tone.Objective,
        language: str = "english",
    ) -> str:
        return f"""
Context:
"{context}"

Main Topic and Subtopic:
Using the latest information available, construct a detailed report on the subtopic: {current_subtopic} under the main topic: {main_topic}.
You must limit the number of subsections to a maximum of {max_subsections}.

Content Focus:
- The report should focus on answering the question, be well-structured, informative, in-depth, and include facts and numbers if available.
- Use markdown syntax and follow the {report_format.upper()} format.
- When presenting data, comparisons, or structured information, use markdown tables to enhance readability.

IMPORTANT:Content and Sections Uniqueness:
- This part of the instructions is crucial to ensure the content is unique and does not overlap with existing reports.
- Carefully review the existing headers and existing written contents provided below before writing any new subsections.
- Prevent any content that is already covered in the existing written contents.
- Do not use any of the existing headers as the new subsection headers.
- Do not repeat any information already covered in the existing written contents or closely related variations to avoid duplicates.
- If you have nested subsections, ensure they are unique and not covered in the existing written contents.
- Ensure that your content is entirely new and does not overlap with any information already covered in the previous subtopic reports.

"Existing Subtopic Reports":
- Existing subtopic reports and their section headers:

    {existing_headers}

- Existing written contents from previous subtopic reports:

    {relevant_written_contents}

"Structure and Formatting":
- As this sub-report will be part of a larger report, include only the main body divided into suitable subtopics without any introduction or conclusion section.

- You MUST include markdown hyperlinks to relevant source URLs wherever referenced in the report, for example:

    ### Section Header

    This is a sample text ([in-text citation](url)).

- Use H2 for the main subtopic header (##) and H3 for subsections (###).
- Use smaller Markdown headers (e.g., H2 or H3) for content structure, avoiding the largest header (H1) as it will be used for the larger report's heading.
- Organize your content into distinct sections that complement but do not overlap with existing reports.
- When adding similar or identical subsections to your report, you should clearly indicate the differences between and the new content and the existing written content from previous subtopic reports. For example:

    ### New header (similar to existing header)

    While the previous section discussed [topic A], this section will explore [topic B]."

"Date":
Assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.

"IMPORTANT!":
- You MUST write the report in the following language: {language}.
- The focus MUST be on the main topic! You MUST Leave out any information un-related to it!
- Must NOT have any introduction, conclusion, summary or reference section.
- You MUST use in-text citation references in {report_format.upper()} format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).
- You MUST mention the difference between the existing content and the new content in the report if you are adding the similar or same subsections wherever necessary.
- The report should have a minimum length of {total_words} words.
- Use an {tone.value} tone throughout the report.

Do NOT add a conclusion section.
"""

    @staticmethod
    def generate_draft_titles_prompt(
        current_subtopic: str,
        main_topic: str,
        context: str,
        max_subsections: int = 5
    ) -> str:
        return f"""
"Context":
"{context}"

"Main Topic and Subtopic":
Using the latest information available, construct a draft section title headers for a detailed report on the subtopic: {current_subtopic} under the main topic: {main_topic}.

"Task":
1. Create a list of draft section title headers for the subtopic report.
2. Each header should be concise and relevant to the subtopic.
3. The header should't be too high level, but detailed enough to cover the main aspects of the subtopic.
4. Use markdown syntax for the headers, using H3 (###) as H1 and H2 will be used for the larger report's heading.
5. Ensure the headers cover main aspects of the subtopic.

"Structure and Formatting":
Provide the draft headers in a list format using markdown syntax, for example:

### Header 1
### Header 2
### Header 3

"IMPORTANT!":
- The focus MUST be on the main topic! You MUST Leave out any information un-related to it!
- Must NOT have any introduction, conclusion, summary or reference section.
- Focus solely on creating headers, not content.
"""

    @staticmethod
    def generate_report_introduction(question: str, research_summary: str = "", language: str = "english", report_format: str = "apa") -> str:
        return f"""{research_summary}\n
Using the above latest information, Prepare a detailed report introduction on the topic -- {question}.
- The introduction should be succinct, well-structured, informative with markdown syntax.
- As this introduction will be part of a larger report, do NOT include any other sections, which are generally present in a report.
- The introduction should be preceded by an H1 heading with a suitable topic for the entire report.
- You must use in-text citation references in {report_format.upper()} format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).
Assume that the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.
- The output must be in {language} language.
"""


    @staticmethod
    def generate_report_conclusion(query: str, report_content: str, language: str = "english", report_format: str = "apa") -> str:
        """
        Generate a concise conclusion summarizing the main findings and implications of a research report.

        Args:
            query (str): The research task or question.
            report_content (str): The content of the research report.
            language (str): The language in which the conclusion should be written.

        Returns:
            str: A concise conclusion summarizing the report's main findings and implications.
        """
        prompt = f"""
    Based on the research report below and research task, please write a concise conclusion that summarizes the main findings and their implications:

    Research task: {query}

    Research Report: {report_content}

    Your conclusion should:
    1. Recap the main points of the research
    2. Highlight the most important findings
    3. Discuss any implications or next steps
    4. Be approximately 2-3 paragraphs long

    If there is no "## Conclusion" section title written at the end of the report, please add it to the top of your conclusion.
    You must use in-text citation references in {report_format.upper()} format and make it with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url)).

    IMPORTANT: The entire conclusion MUST be written in {language} language.

    Write the conclusion:
    """

        return prompt


## Factory ######################################################################

# This is the function signature for the various prompt generator functions
PROMPT_GENERATOR = Callable[
    [
        str,        # question
        str,        # context
        str,        # report_source
        str,        # report_format
        str | None, # tone
        int,        # total_words
        str,        # language
    ],
    str,
]

report_type_mapping = {
    ReportType.ResearchReport.value: "generate_report_prompt",
    ReportType.ResourceReport.value: "generate_resource_report_prompt",
    ReportType.OutlineReport.value: "generate_outline_report_prompt",
    ReportType.CustomReport.value: "generate_custom_report_prompt",
    ReportType.SubtopicReport.value: "generate_subtopic_report_prompt",
    ReportType.DeepResearch.value: "generate_deep_research_prompt",
}


def get_prompt_by_report_type(
    report_type: str,
    prompt_family: type[PromptFamily] | PromptFamily,
):
    prompt_by_type = getattr(prompt_family, report_type_mapping.get(report_type, ""), None)
    default_report_type = ReportType.ResearchReport.value
    if not prompt_by_type:
        warnings.warn(
            f"Invalid report type: {report_type}.\n"
            f"Please use one of the following: {', '.join([enum_value for enum_value in report_type_mapping.keys()])}\n"
            f"Using default report type: {default_report_type} prompt.",
            UserWarning,
        )
        prompt_by_type = getattr(prompt_family, report_type_mapping.get(default_report_type))
    return prompt_by_type


prompt_family_mapping = {
    PromptFamilyEnum.Default.value: PromptFamily,
}


def get_prompt_family(
    prompt_family_name: PromptFamilyEnum | str, config: Config,
) -> PromptFamily:
    """Get a prompt family by name or value."""
    if isinstance(prompt_family_name, PromptFamilyEnum):
        prompt_family_name = prompt_family_name.value
    if prompt_family := prompt_family_mapping.get(prompt_family_name):
        return prompt_family(config)
    warnings.warn(
        f"Invalid prompt family: {prompt_family_name}.\n"
        f"Please use one of the following: {', '.join([enum_value for enum_value in prompt_family_mapping.keys()])}\n"
        f"Using default prompt family: {PromptFamilyEnum.Default.value} prompt.",
        UserWarning,
    )
    return PromptFamily()
