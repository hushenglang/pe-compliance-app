1. LLM with tavily search tool to improve the news summary from all different other sources
2.integrate with other news sources, like HKEX, HKMA, etc.
3. alicloud infra.
    - RDS Mysql HK Region 1CUP1GB
    - backend server: slight ECS HK Region yearly/monthly payment
    - frontend server: CDN or site hosting service, need to check?
    - domain name: buy one, need to check?
    - ssl certificate: buy one, need to check?
4. in news table, add a column to store news status, if it is already processed. Processed means the news is already emailed or discarded.

done: HKMA: https://www.hkma.gov.hk/eng/news-and-media/press-releases/
done: HKEX: https://www.hkex.com.hk/News/Regulatory-Announcements?sc_lang=en
done: CSRC: http://www.csrc.gov.cn/csrc/c100039/common_list.shtml
SEC: https://www.sec.gov/newsroom/press-releases



