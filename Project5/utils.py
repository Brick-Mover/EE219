import json
import pickle
import re
import numpy as np
from datetime import date
import matplotlib.pyplot as plt
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
import nltk
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.metrics import accuracy_score, recall_score, precision_score
import itertools
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import TruncatedSVD

def fileLocation(category):
    return 'tweet_data/tweets_%s.txt' % category


def save_obj(name, obj):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


def tsDiffHour(startTs:int, endTs:int) -> int:
    """
    startTs: the rounded(down) timestamp of the first tweet
    endTs: the raw timestamp of a tweet
    :return: the hour difference between startTs and endTs(0 -> ...)
    """
    return (endTs // 3600 * 3600 - startTs) // 3600


def extractFirstTsAndLastTs():
    """
    This function is only called once to extract the first timestamp of each category.
    Included for the completeness of code submission.
    """
    hashtags = ['#gohawks', '#nfl', '#sb49', '#gopatriots', '#patriots', '#superbowl']
    for category in hashtags:
        with open(fileLocation(category), encoding="utf8") as f:
            tweets = f.readlines()
            firstTs = json.loads(tweets[0])['citation_date']
            lastTs = firstTs
            for t in tweets:
                t = json.loads(t)
                if t['citation_date'] < firstTs:
                    firstTs = t['citation_date']
                if t['citation_date'] > lastTs:
                    lastTs = t['citation_date']
            print(category, firstTs, lastTs)

# 
# for function days_of_account
# 
month_num = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12
}

def days_of_account(t):
    account_date = t['tweet']['user']['created_at'].split(' ')
    post_date = t['tweet']['created_at'].split(' ')
    d_account = date(int(account_date[5]), month_num[account_date[1]],
                     int(account_date[2]))
    d_post = date(int(post_date[5]), month_num[post_date[1]],
                     int(post_date[2]))
    return (d_post-d_account).days

# 
# feat = 'retweet', 'follower', 'mention' (for mention count sum), 
# 'rank_score', 'passitivity' (rareness, as defined in report, for sum),
# and 'tags' (for sum), 'author' (for unique author count)
# 
def get_feature(tweet, feat):
    if feat == 'retweet':
        return tweet['metrics']['citations']['total']
    elif feat == 'follower':
        return tweet['author']['followers']
    elif feat == 'mention':
        return len(tweet['tweet']['entities']['user_mentions'])
    elif feat == 'rank_score':
        return tweet['metrics']['ranking_score']
    elif feat == 'passitivity':
        days_account = days_of_account(tweet)
        followers = tweet['tweet']['user']['followers_count']
        res = days_account/(1.0+followers)
        return res
    elif feat == 'tags':
        res = len(tweet['tweet']['entities']['hashtags'])
        return res
    elif feat == 'author':
        return tweet['author']['name']


# 
# create X (new features) for Q1_3
# 
def createData():
    hashtags = ['#gohawks', '#nfl', '#sb49', '#gopatriots', '#patriots', '#superbowl']
    for tag in hashtags:
        with open(fileLocation(tag), encoding="utf8") as f:
            tweets = f.readlines()
            firstTs = FIRST_TS[tag]
            firstTs = firstTs // 3600 * 3600
            lastTs = LAST_TS[tag]
            totalHours = tsDiffHour(firstTs, lastTs) + 1

            mentionCount = [0] * totalHours
            rankScore = [0] * totalHours
            passitivity = [0] * totalHours
            tags = [0] * totalHours
            author = [0] * totalHours
            uniq_author = {}

            for tweet in tweets:
                t = json.loads(tweet)
                ts = t['citation_date']
                hourDiff = tsDiffHour(firstTs, ts)
                
                mentionCount[hourDiff] += get_feature(t, 'mention')
                rankScore[hourDiff] += get_feature(t, 'rank_score')
                passitivity[hourDiff] += get_feature(t, 'passitivity')
                tags[hourDiff] += get_feature(t, 'tags')
                aut = get_feature(t, 'author')
                if aut not in uniq_author:
                    uniq_author[aut] = len(uniq_author)
                    author[hourDiff] += 1
            
            X = np.array([mentionCount, rankScore, passitivity, tags, author])
            X = X.transpose()
            save_obj(tag + '_Q13', X)


def make_plot(x, ys, scatter=False, bar=False, xlabel=None, ylabel=None, 
              xticks=None, grid=False, title=None, 
              size_marker = 20, marker = '.'):
    for y, label in ys:
        if scatter:
            plt.scatter(x, y, s=size_marker, marker=marker, label=label)
        elif bar:
            plt.bar(x, y, label=label, color='g', width=1)
        else:
            plt.plot(x, y, label=label)
    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)
    if xticks is not None:
        plt.xticks(x)
    plt.legend()
    if grid == True:
        plt.grid()
    if title is not None:
        plt.title(title)
    plt.show() 

def match(l):
    if (re.match('.*WA.*', l) or re.match('.*Wash.*', l)):
        return 0
    if (re.match('.*MA.*', l) or re.match('.*Mass.*', l)):
        return 1
    return -1

class mytokenizer(object):
    def __init__(self):
        self.stemmer = SnowballStemmer("english", ignore_stopwords=True)
        self.tokenizer = RegexpTokenizer(r'\w+')

    def __call__(self, text):
        tokens = re.sub(r'[^A-Za-z]', " ", text)
        tokens = re.sub("[,.-:/()?{}*$#&]"," ",tokens)
        tokens =[word for tk in nltk.sent_tokenize(tokens) for word in nltk.word_tokenize(tk)]
        new_tokens = []
        for token in tokens:
            if re.search('[a-zA-Z]{2,}', token):
                new_tokens.append(token)     
        stems = [self.stemmer.stem(t) for t in new_tokens]
        return stems

def createQ2Data():
    loc = np.array([]) #y
    text_data = np.array([]) #X
    with open(fileLocation(tag), encoding="utf8") as f:
        tweets = f.readlines()

        count = 0 
        count_loc = 0
        for tweet in tweets:
    #         if count%10000 == 0:
    #             print('count ',count)
            count+=1
            t = json.loads(tweet)
            location = t['tweet']['user']['location']
            mat_res = match(location)
            if mat_res != -1:
    #             if count_loc%1000 == 0:
    #                 print('count_loc ',count_loc)
                count_loc += 1
                text = t['tweet']['text']
                loc = np.append(loc, mat_res)
                text_data = np.append(text_data, text)

    TFidf = TfidfVectorizer(analyzer='word',tokenizer=mytokenizer(), 
                            stop_words=ENGLISH_STOP_WORDS, 
                            norm = 'l2', max_df=0.9, min_df=2)
    svd = TruncatedSVD(n_components=50)
    X = svd.fit_transform(TFidf.fit_transform(text_data))

    # save_obj('text_data_Q2', text_data)
    save_obj('label_Q2', loc)
    save_obj('X_Q2', X)



def plot_confusion_matrix(label_true, label_pred, classname, normalize=False, title='Confusion Matrix'):
    plt.figure()
    cmat = confusion_matrix(label_true, label_pred)
    cmap = plt.cm.Blues
    plt.imshow(cmat, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    tick_marks = np.arange(len(classname))
    plt.xticks(tick_marks, classname, rotation=45)
    plt.yticks(tick_marks, classname)

    if normalize:
        cmat = cmat.astype('float') / cmat.sum(axis=1)[:, np.newaxis]

    # print(cmat)

    thresh = cmat.max() / 2.
    for i, j in itertools.product(range(cmat.shape[0]), range(cmat.shape[1])):
        if normalize == False:
            plt.text(j, i, cmat[i, j], horizontalalignment="center", color="white" if cmat[i, j] > thresh else "black")
        else:
            plt.text(j, i, "%.2f"%cmat[i, j], horizontalalignment="center", color="white" if cmat[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()

# 
# if score is true, return y_score for usage in plot of ROC
# ! Only set score to True if the classifier has function predict_proba!!!
# 
def cross_val(clf, X, y, shuffle=False, score=False, verbose=False):
    kf = KFold(n_splits=10, shuffle = shuffle)

    y_true_train = np.array([])
    y_pred_train = np.array([])
    y_true_test = np.array([])
    y_pred_test = np.array([])
    if score == True:
        y_score_train = np.array([])
        y_score_test = np.array([])
    X = np.array(X)
    y = np.array(y)
    epoch = 1
    for train_index, test_index in kf.split(X):
        if verbose:
            print('epoch', epoch)
        epoch += 1
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        clf.fit(X_train, y_train)
        sub_y_pred_test = clf.predict(X_test)
        sub_y_pred_train = clf.predict(X_train)

        y_true_test = np.append(y_true_test, y_test)
        y_true_train = np.append(y_true_train, y_train)
        y_pred_test = np.append(y_pred_test, sub_y_pred_test)
        y_pred_train = np.append(y_pred_train, sub_y_pred_train)

        if score == True:
            sub_y_score_train = clf.predict_proba(X_train)
            sub_y_score_test = clf.predict_proba(X_test)
            y_score_train = np.append(y_score_train, sub_y_score_train)
            y_score_test = np.append(y_score_test, sub_y_score_test)

    if score == True:
        return y_true_train, y_pred_train, y_true_test, y_pred_test, y_score_train, y_score_test
    else:
        return y_true_train, y_pred_train, y_true_test, y_pred_test

# 
# calculate accuracy score and f1 score
# 
def metrics(y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    return acc, rec, prec

# 
# return area under curve
# 
def plot_ROC(yTrue, yScore, title='ROC Curve', rang=4, no_score=False):
    # pay attention here
    yScore = yScore.reshape(len(yTrue), 2)
    yScore = yScore[:,1]
    fpr, tpr, _ = roc_curve(yTrue, yScore)
    roc_auc = auc(fpr, tpr)
    lw=2
    plt.plot(fpr, tpr, color='darkorange', lw=lw, label='ROC curve (area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend(loc="lower right")
    plt.show()
    plt.close()

    return roc_auc
