BEGIN TRANSACTION;

CREATE TABLE papers (
    Title text,
    Authors text,
    Abstract text,
    Link text,
    Count_proposed integer,
    Proposed_current_vote integer,
    Discussion text,
    Submitters text
);

CREATE TABLE authors (
    Name text,
    Homepage text,
    CV text
);

CREATE TABLE users (
    Name text,
    Submissions integer,
    Discussed_submissions text,
    Discussion_comments integer
);

COMMIT;
