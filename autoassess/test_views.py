__author__ = 'moonkey'

from django.shortcuts import render, redirect, Http404, HttpResponse
from diagnose.util.wikipedia import DisambiguationError
from diagnose import diagnose
from diagnose.util.wikipedia_util import WikipediaWrapper
from django.views.decorators.clickjacking import xframe_options_exempt
from question_db import *
import json
import answer_db
from visitorlog import log_visitor_ip

from diagnose.version_list import *
import string


@xframe_options_exempt
def consent_form(request):
    request_data = {}
    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = request.POST

    response_data = {}

    return render(request, 'test_pages/consent_form.html', response_data)


@xframe_options_exempt
def single_question(request):
    """
    The intro view\n
    Requires Input: a search term in request.GET["q"].
    ========= Preview ============
    GET /autoassess/single_question?q=Reinforcement+learning
    &assignmentId=ASSIGNMENT_ID_NOT_AVAILABLE
    &hitId=3RKHNXPHGVV4TMFBNBL8TQP4MT8KU9
    ======= Question form ========
    GET
    """
    log_visitor_ip(request)
    request_data = {}
    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = request.POST

    response_data = {}

    # ###### read data from request
    if 'q' not in request_data or not request_data['q']:
        raise Http404
    search_term = request_data['q']

    version = MTURK_QUESTION_VERSION
    if 'v' in request_data:
        if request_data['v'] == 'c':
            version = CURRENT_QUESTION_VERSION
        else:
            version = float(request_data['v'])

    if 'assignmentId' not in request_data:
        # user visiting mode not from mturk
        response_data['assignmentId'] = None
        response_data['hitId'] = None
    else:
        assignmentId = request_data['assignmentId'].strip(" ")
        hitId = request_data['hitId']

        if "ASSIGNMENT_ID_NOT_AVAILABLE" == assignmentId:
            # preview mode
            response_data['assignmentId'] = assignmentId
            response_data['hitId'] = hitId
        else:
            # question form mode
            workerId = request_data['workerId']
            turkSubmitTo = request_data['turkSubmitTo']

            response_data['assignmentId'] = assignmentId
            response_data['hitId'] = hitId
            response_data['workerId'] = workerId
            response_data['turkSubmitTo'] = turkSubmitTo
    ############################

    try:
        try:
            # the search term may not corresponds to a wikipedia entry
            try:
                wiki_topic = WikipediaWrapper.page(search_term).title
            except Exception as e:
                # if connecting to wikipedia server fails
                wiki_topic = search_term
            questions = [load_question(wiki_topic, version=version)]
        except IndexError as e:
            # this is the error it will raise if no questions is founded
            # if there is not questions for this topic in the database
            # then generate and save
            questions = diagnose.diagnose(
                search_term,
                generate_prereq_question=False,
                num_prereq=3,
                version=version)
            save_diagnose_question_set(
                questions,
                version=version,
                force=True)
    except DisambiguationError as dis:
        raise dis

    response_data['quiz'] = questions
    response_data['search_term'] = search_term

    return render(request, 'autoassess/single_question.html', response_data)


@xframe_options_exempt
def single_question_submit(request):
    request_data = {}
    if request.method == 'GET':
        request_data = request.GET.dict()
    elif request.method == 'POST':
        request_data = request.POST.dict()
    response_data = {}

    # This is not used here for now
    main_topic = request_data.pop('main_topic')

    request_data.pop("csrfmiddlewaretoken", None)

    answer_db.save_single_answer(request_data)

    # return HttpResponse(result.text)
    return HttpResponse(
        json.dumps(response_data), content_type="application/json")


@xframe_options_exempt
def multiple_questions_submit(request):
    request_data = {}
    if request.method == 'GET':
        request_data = request.GET.dict()
    elif request.method == 'POST':
        request_data = request.POST.dict()
    response_data = {}

    # This is not used here for now
    main_topic = request_data.pop('main_topic')

    request_data.pop("csrfmiddlewaretoken", None)

    answer_db.save_answers(request_data)

    # return HttpResponse(result.text)
    return HttpResponse(json.dumps(response_data),
                        content_type="application/json")


@xframe_options_exempt
def multiple_questions_single_update(request):
    request_data = {}
    if request.method == 'GET':
        request_data = request.GET.dict()
    elif request.method == 'POST':
        request_data = request.POST.dict()
    response_data = {}

    # This is not used here for now
    main_topic = request_data.pop('main_topic')

    request_data.pop("csrfmiddlewaretoken", None)

    answer_db.save_or_update_question_answer(request_data)

    # return HttpResponse(result.text)
    return HttpResponse(json.dumps(response_data),
                        content_type="application/json")


@xframe_options_exempt
def multiple_questions(request):
    """

    :param request:
    :return:
    """
    log_visitor_ip(request)

    request_data = {}
    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = request.POST

    response_data = {}

    # ###### read data from request
    if 'q' not in request_data or not request_data['q']:
        raise Http404
    search_term = request_data['q']


    set_type = CURRENT_QUESTION_SET
    if 's' in request_data:
        if request_data['s'].lower() == 'm':
            set_type = SET_MENTIONED
        if request_data['s'].lower() == 'p':
            set_type = SET_PREREQ

    version = MTURK_QUESTION_VERSION
    if 'v' in request_data:
        if request_data['v'] == 'c':
            version = CURRENT_QUESTION_VERSION
        else:
            version = float(request_data['v'])

    if version < 0:
        set_type = SET_SELF_DEFINED

    if 'assignmentId' not in request_data:
        # user visiting mode not from mturk
        response_data['hitId'] = None

        response_data['assignmentId'] = "EDUWIKI_"+id_generator()
        response_data['workerId'] = "EDUWIKI_"+id_generator()
        response_data['turkSubmitTo'] = '/'
    else:
        assignmentId = request_data['assignmentId'].strip(" ")
        hitId = request_data['hitId']

        if "ASSIGNMENT_ID_NOT_AVAILABLE" == assignmentId:
            # preview mode
            response_data['assignmentId'] = assignmentId
            response_data['hitId'] = hitId
        else:
            # question form mode
            workerId = request_data['workerId']
            turkSubmitTo = request_data['turkSubmitTo']

            response_data['assignmentId'] = assignmentId
            response_data['hitId'] = hitId
            response_data['workerId'] = workerId
            response_data['turkSubmitTo'] = turkSubmitTo
    ############################

    try:
        try:
            # the search term may not corresponds to a wikipedia entry
            #TODO:: change this to google site search with the title in it
            try:
                quiz_topic = search_term
                questions, quiz_id = load_diagnose_question_set(
                    quiz_topic, version=version, set_type=set_type,
                    with_meta_info=True, question_shuffle=True)
            except Exception as e:
                print >> sys.stderr, e
                quiz_topic = WikipediaWrapper.page(search_term).title
                questions, quiz_id = load_diagnose_question_set(
                    quiz_topic, version=version, set_type=set_type,
                    with_meta_info=True, question_shuffle=True)
            # try:
            #     quiz_topic = WikipediaWrapper.page(search_term).title
            # except Exception as e:
            #   #  if connecting to wikipedia server fails
                # quiz_topic = search_term
            # questions, quiz_id = load_diagnose_question_set(
            #     quiz_topic, version=version, set_type=set_type,
            #     with_meta_info=True, question_shuffle=True)

            response_data['quiz_id'] = quiz_id

        except IndexError as e:
            # this is the error it will raise if no questions is founded
            # if there is not questions for this topic in the database
            # then generate and save

            # questions = diagnose.diagnose(
            #     search_term,
            #     generate_prereq_question=False,
            #     num_prereq=3,
            #     version=version,
            #     set_type=set_type)
            # save_diagnose_question_set(
            #     questions,
            #     version=version,
            #     force=True,
            #     set_type=set_type)

            # Do not generate question on server side
            raise Http404("Page Not Found. Please contact webmaster to fix.")

    except DisambiguationError as dis:
        raise dis

    response_data['quiz'] = questions
    response_data['search_term'] = search_term

    response_data['question_order'] = [str(q['id']) for q in questions]

    return render(request, 'autoassess/multiple_questions.html', response_data)


def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
