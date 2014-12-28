# db layout
TABLE papers
    title text
    authors text
    abstract text
    link text
    count_proposed integer
    proposed_current_vote integer
    discussion text
    submitters text

TABLE authors
    name text
    cv text
    homepage text

TABLE users
    name text
    submissions integer
    discussed_submissions text
    discussion_comments integer
