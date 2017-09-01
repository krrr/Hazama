#include <tuple>
#include <QPainter>
#include <QLineEdit>
#include <QHBoxLayout>
#include "taglistdelegates.h"
#include "customobjects/elidelabel.h"
#include "globals.h"

QWidget *TagDelegateBase::createEditor(QWidget *parent, const QStyleOptionViewItem &opt, const QModelIndex &idx) const {
    auto e = qobject_cast<QLineEdit*>(QItemDelegate::createEditor(parent, opt, idx));
    e->setObjectName("tagListEdit");
    e->setProperty("oldText", idx.data().toString());
    return e;
}

void TagDelegateBase::updateEditorGeometry(QWidget *editor, const QStyleOptionViewItem &opt, const QModelIndex &) const {
    editor->setGeometry(opt.rect);
}


TagDelegate::TagDelegate(QObject *parent) : TagDelegateBase(parent) {
    h = fontMetric(fonts.app).height() + 8;
    showCount = settings->value("tagListCount").toBool();
}

void TagDelegate::paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const {
    int x=opt.rect.x(), y=opt.rect.y(), w=opt.rect.width();
    auto tag = idx.data(Qt::DisplayRole).toString();
    auto count = QString::number(idx.data(Qt::UserRole).toInt());
    p->setFont(fonts.app);
    bool selected = opt.state & QStyle::State_Selected;
    auto textArea = QRect(x+4, y, w-8, h);
    if (idx.row() == 0)  { // row 0 is always All(clear tag filter)
        p->setPen(QColor(80, 80, 80));
        p->drawText(textArea, Qt::AlignVCenter|Qt::AlignLeft, tag);
    } else {
        p->setPen(QColor(209, 109, 63));
        p->drawLine(x, y, w, y);
        if (selected) {
            p->setPen(QColor(181, 61, 0));
            p->setBrush(QColor(250, 250, 250));
            p->drawRect(x, y+1, w-1, h-2);
        }
        // draw tag
        p->setPen((selected) ? QColor(20, 20, 20) : QColor(80, 80, 80));
        auto elided = fontMetric(fonts.app).elidedText(
            tag, Qt::ElideRight,
            (showCount) ? w-fontMetric(fonts.datetime).width(count)-12 : w-12);
        p->drawText(textArea, Qt::AlignVCenter|Qt::AlignLeft, elided);
        // draw tag count
        if (showCount)
            p->setFont(fonts.datetime);
            p->drawText(textArea, Qt::AlignVCenter|Qt::AlignRight, count);
    }
}


QSize TagDelegate::sizeHint(const QStyleOptionViewItem &, const QModelIndex &) const {
    return QSize(-1, h);
}

void TagDelegate::updateEditorGeometry(QWidget *editor, const QStyleOptionViewItem &opt, const QModelIndex &) const {
    auto rect = opt.rect;
    rect.translate(1, 1);
    rect.setWidth(rect.width() - 2);
    rect.setHeight(rect.height() - 1);
    editor->setGeometry(rect);
}



class ColorfulItem : public QFrame {
public:
    ElideLabel *name;
    QLabel *count;
    std::tuple<bool, bool> lastSetProperties = std::make_tuple(false, false);

    ColorfulItem(QWidget *parent=nullptr) : QFrame(parent) {
        setObjectName("TagListItem");
        auto hLayout = new QHBoxLayout(this);
        hLayout->setContentsMargins(0, 0, 0, 0);

        name = new ElideLabel(this);
        name->setObjectName("TagListItemName");
        count = new QLabel(this);
        count->setObjectName("TagListItemCount");
        count->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Preferred);
        hLayout->addWidget(name);
        hLayout->addWidget(count);
    }
};


TagDelegateColorful::TagDelegateColorful(QObject *parent) : TagDelegateBase(parent) {
    showCount = settings->value("tagListCount").toBool();
    itemWidget = new ColorfulItem();
    itemWidget->setFixedHeight(itemWidget->sizeHint().height());
    if (!showCount)
        itemWidget->count->hide();
}

TagDelegateColorful::~TagDelegateColorful() {
    delete itemWidget;
}

void TagDelegateColorful::paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const {
    itemWidget->name->setText(idx.data(Qt::DisplayRole).toString());
    itemWidget->count->setVisible(idx.row() != 0);
    if (showCount && idx.row() != 0)
        itemWidget->count->setText(QString::number(idx.data(Qt::UserRole).toInt()));

    std::tuple<bool, bool> properties = std::make_tuple(
                opt.state & QStyle::State_Selected,
                opt.state & QStyle::State_Active);
    if (itemWidget->lastSetProperties != properties) {
        itemWidget->setProperty("selected", std::get<0>(properties));
        itemWidget->setProperty("active", std::get<1>(properties));
        itemWidget->lastSetProperties = properties;
        refreshStyle(itemWidget);
    }
    if (itemWidget->size() != opt.rect.size())
        itemWidget->resize(opt.rect.size());

    p->translate(opt.rect.topLeft());
    itemWidget->render(p, QPoint());
    p->resetTransform();
}

QSize TagDelegateColorful::sizeHint(const QStyleOptionViewItem &, const QModelIndex &) const {
    return QSize(-1, itemWidget->height());
}
