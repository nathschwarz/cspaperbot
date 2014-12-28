BEGIN TRANSACTION;
INSERT INTO 'papers' ('Title','Authors','Abstract','Link','Count_proposed','Proposed_current_vote','Discussion','Submitters') VALUES
    (
        'Dummy paper 01',
        'Dummy Author Sr., Dummy Author Jr.',
        'Very short and undescriptive abstract of dummy paper 01',
        'https://link.to/a/dummy/paper.pdf',
        4,
        1,
        '',
        'cspaperbot, dummyuser'
    ),
    (
        'Dummy paper 02',
        'Dummy Author Jr., Prof. Paper-Leecher',
        'Very short and undescriptive abstract of dummy paper 02',
        'https://link.to/a/dummy/paper.pdf',
        1,
        1,
        '',
        'dummyuser'
    );

INSERT INTO 'authors' ('Name', 'CV', 'Homepage') VALUES
    (
        'Dummy Author Jr.',
        'https://authorjr.com/cv.pdf',
        'https://authorjr.com'
    ),
    (
        'Dummy Author Sr.',
        'https://elite-uni.com/authorsr/cv.pdf',
        'https://elite-uni.com/authorsr'
    ),
    (
        'Paul Paper-Leecher',
        'https://paper-leecher.com/cv.pdf',
        'https://paper-leecher.com/'
    );

INSERT INTO 'users' ('Name', 'submissions', 'Discussed_submissions', 'Discussion_comments') VALUES
    (
        'cspaperbot',
        1,
        'Dummy paper 01',
        0
    ),
    (
        'dummyuser',
        2,
        '',
        0
    );

COMMIT;
