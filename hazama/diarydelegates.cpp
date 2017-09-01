#include <QPainter>
#include <QtGlobal>
#include <QLabel>
#include <QToolButton>
#include <QAbstractTextDocumentLayout>
#include <QBoxLayout>
#include <QPainterPath>
#include "globals.h"
#include "diarymodel.h"
#include "diarydelegates.h"
#include "customobjects/elidelabel.h"
#include "customobjects/multilineelidelabel.h"


DiaryDelegate::DiaryDelegate(QObject *parent) : QAbstractItemDelegate(parent) {
    // Because some fonts have much more space at top and bottom, we use ascent instead
    // of height, and add it with a small number.
    int magic = 5 * scaleRatio;
    titleH = qMax(fontMetric(fonts.title).ascent(), fontMetric(fonts.datetime).ascent()) + magic;
    titleAreaH = titleH + 4;
    textH = fontMetric(fonts.text).lineSpacing() * 4;
    tagPathH = fontMetric(fonts.app).ascent() + magic;
    tagPathH += tagPathH % 2;  // can be divided by 2
    tagH = tagPathH + 4;
    dtW = fontMetric(fonts.datetime).width(datetimeTrans("2000-01-01 00:00")) + 40;

    // doc is used to draw text(diary's body)
    doc = new NTextDocument(this);
    doc->setDefaultFont(fonts.text);
    doc->setUndoRedoEnabled(false);
    doc->setDocumentMargin(0);
    doc->documentLayout()->setPaintDevice(qobject_cast<QWidget*>(parent));  // HiDPI screen

    // setup colors
    textC = Qt::black;
    bgC = QColor(255, 236, 176);
    borderC = QColor(214, 172, 41);
    inActBgC = QColor(255, 236, 176, 40);
    grayC = QColor(93, 73, 57);
}

void DiaryDelegate::paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const {
    int x=opt.rect.x(), y=opt.rect.y(), w=opt.rect.width();
    const auto diary = idx.data().value<Diary>();
    bool selected = opt.state & QStyle::State_Selected;
    bool active = opt.state & QStyle::State_Active;
    int allH = titleAreaH + 2 + textH + ((diary.tags.isEmpty())? 0 : tagH) + 6;

    // draw border and background
    p->setPen(borderC);
    p->setBrush((selected && active) ? bgC : inActBgC);
    p->drawRect(x+1, y, w-2, allH);  // outer border
    if (selected) {  // draw inner border
        QPen pen;
        pen.setStyle(Qt::DashLine);
        pen.setColor(grayC);
        p->setPen(pen);
        p->drawRect(x+2, y+1, w-4, allH-2);
    }
    // draw datetime and title
    p->setPen(grayC);
    p->drawLine(x+10, y+titleAreaH, x+w-10, y+titleAreaH);
    p->setPen(textC);
    p->setFont(fonts.datetime);
    p->drawText(x+14, y+titleAreaH-titleH, dtW, titleH,
                Qt::AlignVCenter, datetimeTrans(diary.datetime));
    if (diary.title.size()) {
        p->setFont(fonts.title);
        int titleW = w - dtW - 13;
        QString title = fontMetric(fonts.title).elidedText(diary.title, Qt::ElideRight, titleW);
        p->drawText(x+dtW, y+titleAreaH-titleH, titleW, titleH,
                    Qt::AlignVCenter|Qt::AlignRight, title);
    }
    // draw text
    doc->setText(diary.text);
    doc->setTextFormats(diary.formats);
    doc->setTextWidth(w - 26);
    p->translate(x+14, y+titleAreaH+2);
    doc->drawContentsColor(p, QRect(0, 0, w-26, textH), textC);
    p->resetTransform();
    // draw tags
    if (!diary.tags.isEmpty()) {
        p->setPen(grayC);
        p->setFont(fonts.app);
        p->translate(x+15, y+titleAreaH+6+textH);
        int realX=x+15, maxX=w-10;
        bool elide = false;
        for (auto &t : diary.tags) {
            int tagW = fontMetric(fonts.app).width(t) + 4;
            realX += tagW + 15;
            if (realX > maxX) {
                elide = true;
                break;
            }
            QPainterPath tagPath;
            int half = tagPathH / 2;
            tagPath.moveTo(half, 0);
            tagPath.lineTo(half+tagW, 0);
            tagPath.lineTo(half+tagW, tagPathH);
            tagPath.lineTo(half, tagPathH);
            tagPath.lineTo(0, half);
            tagPath.closeSubpath();
            p->drawPath(tagPath);
            p->drawText(half, 0, tagW, tagPathH, Qt::AlignCenter, t);
            p->translate(tagW+15, 0);  // translate by offset
        }
        if (!elide) {
            p->resetTransform();
            return;
        }
        // draw ellipsis if too many tags
        p->setPen(Qt::DotLine);
        p->drawLine(-4, tagPathH/2, 2, tagPathH/2);
        p->resetTransform();
    }
}

QSize DiaryDelegate::sizeHint(const QStyleOptionViewItem &, const QModelIndex &idx) const {
    const auto diary = idx.data().value<Diary>();
    int allH = titleAreaH + 2 + textH + ((diary.tags.isEmpty())? 0 : tagH) + 6;
    return QSize(-1, allH+3);  // 3 is spacing between entries
}


// Widget that used to draw an item in paint method.
class ColorfulDiaryItem : public QFrame {
public:
    ElideLabel *title, *tag;
    QLabel *datetime;
    MultiLineElideLabel *text;
    QToolButton *datetimeIco, *tagIco;
    QBoxLayout *vLayout0, *hLayout0, *hLayout1;
    std::tuple<bool, bool> lastSetProperties = std::make_tuple(false, false);

    ColorfulDiaryItem() : QFrame() {
        setObjectName("DiaryListItem");
        title = new ElideLabel(this);
        title->setObjectName("DiaryListItemTitle");
        title->setFont(fonts.title);
        title->setAlignment(Qt::AlignVCenter | Qt::AlignRight);
        title->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
        datetime = new QLabel(this);
        datetime->setObjectName("DiaryListItemDt");
        datetime->setFont(fonts.datetime);
        datetime->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Preferred);

        text = new MultiLineElideLabel(this);
        text->setObjectName("DiaryListItemText");
        text->setMaximumLineCount(settings->value("previewLines").toInt());
        text->setFont(fonts.text);

        tag = new ElideLabel(this);
        tag->setObjectName("DiaryListItemTag");
        // use QToolButton to display icons
        datetimeIco = new QToolButton(this);
        datetimeIco->setObjectName("DiaryListItemDtIco");
        int minSz = qMax(fontMetric(fonts.datetime).ascent(), int(12*scaleRatio));
        datetimeIco->setIconSize(QSize(minSz, minSz));
        datetimeIco->setIcon(QIcon(":/calendar.png"));

        tagIco = new QToolButton(this);
        tagIco->setObjectName("DiaryListItemTagIco");
        minSz = qMax(fontMetric(fonts.app).ascent(), int(12*scaleRatio));
        tagIco->setIconSize(QSize(minSz, minSz));
        tagIco->setIcon(QIcon(":/tag.png"));

        vLayout0 = new QVBoxLayout(this);
        hLayout0 = new QHBoxLayout();
        hLayout1 = new QHBoxLayout();
        for (auto i : {vLayout0, hLayout0, hLayout1}) {
            i->setContentsMargins(0, 0, 0, 0);
            i->setSpacing(0);
        }

        hLayout0->addWidget(datetimeIco);
        hLayout0->addWidget(datetime);
        hLayout0->addWidget(title);
        hLayout0->insertSpacing(2, 10);
        hLayout1->addWidget(tagIco);
        hLayout1->addWidget(tag);
        vLayout0->addLayout(hLayout0);
        vLayout0->addWidget(text);
        vLayout0->addLayout(hLayout1);
    }
};

const QString DiaryDelegateColorful::TAG_SEPARATOR = QString(' ') + QChar(0x2022) + ' ';  // use bullet to separate

DiaryDelegateColorful::DiaryDelegateColorful(QObject *parent) : QAbstractItemDelegate(parent) {
    itemWidget = new ColorfulDiaryItem();
    itemHeightWithTag = itemWidget->sizeHint().height();
    itemHeightNoTag = itemHeightWithTag - itemWidget->hLayout1->sizeHint().height();
}

DiaryDelegateColorful::~DiaryDelegateColorful() {
    delete itemWidget;
}

void DiaryDelegateColorful::paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const {
    const auto diary = idx.data().value<Diary>();
    // Some layout behaviours are full of mystery, be careful!!!!
    itemWidget->datetime->setText(datetimeTrans(diary.datetime));
    itemWidget->title->setText(diary.title);
    itemWidget->text->setText(diary.text);
    if (!diary.tags.isEmpty())
        itemWidget->tag->setText(diary.tags.join(TAG_SEPARATOR));
    itemWidget->tag->setVisible(!diary.tags.isEmpty());
    itemWidget->tagIco->setVisible(!diary.tags.isEmpty());

    if (itemWidget->size() != opt.rect.size())
        itemWidget->resize(opt.rect.size());
    std::tuple<bool, bool> properties = std::make_tuple(
                opt.state & QStyle::State_Selected,
                opt.state & QStyle::State_Active );
    if (itemWidget->lastSetProperties != properties) {
        itemWidget->setProperty("selected", std::get<0>(properties));
        itemWidget->setProperty("active", std::get<1>(properties));
        itemWidget->lastSetProperties = properties;
        refreshStyle(itemWidget);  // must be called after dynamic property changed
    }

    // don't use offset argument of QWidget.render
    p->translate(opt.rect.topLeft());
    // render will activate layouts and send pending resize events
    itemWidget->render(p, QPoint());
    p->resetTransform();
}

QSize DiaryDelegateColorful::sizeHint(const QStyleOptionViewItem &, const QModelIndex &idx) const {
    // an attempt to have real height according to text layout has failed,
    // because program will be unresponsive after width of list changed
    const auto diary = idx.data().value<Diary>();
    return QSize(-1, (diary.tags.isEmpty()) ? itemHeightNoTag : itemHeightWithTag);
}
