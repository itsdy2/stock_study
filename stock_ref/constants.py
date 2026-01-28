OPTS = {
    'home_module': 'analysis',
    'use_db': True,
    'use_default_setting': True,
    'menu': {
        'uri': 'stock_ref',
        'name': '주식 투자 참고',
        'list': [
            {
                'uri': 'base',
                'name': '설정',
                'list': [
                    {'uri': 'setting', 'name': '기본 설정'},
                ]
            },
            {
                'uri': 'analysis',
                'name': '분석',
                'list': [
                    {'uri': 'dashboard', 'name': '대시보드'},
                    {'uri': 'list', 'name': 'ETF 상대강도'},
                ]
            }
        ]
    },
    'default_route': 'normal',
}
