import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import "../components"
import ".."

Item {
    id: root
    property string zedState: backend.systemStatus.zed || "stopped"
    property bool zedRunning: zedState === "running" || zedState === "embedded"
    function streamColor(state) {
        if (state === "ok") return Theme.success
        if (state === "camera_off") return Theme.muted
        return Theme.warning
    }

    Component.onCompleted: backend.setCameraPreviewActive(true)
    Component.onDestruction: backend.setCameraPreviewActive(false)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.pageMargin
        spacing: 12

        Label { text: "相机画面"; color: Theme.text; font.pixelSize: 26; font.bold: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            StatusCard {
                Layout.fillWidth: true
                title: "ZED 进程"
                value: backend.localizedStatus(backend.systemStatus.zed || "stopped")
                statusColor: Theme.stateColor(root.zedState)
            }
            StatusCard {
                Layout.fillWidth: true
                title: "画面状态"
                value: backend.cameraStreamText
                statusColor: root.streamColor(backend.cameraStreamState)
            }
            WarmButton {
                objectName: "startCameraButton"
                text: "开启相机"
                enabled: !root.zedRunning && backend.cameraStreamState !== "ok"
                Layout.preferredWidth: 140
                Layout.preferredHeight: Theme.minimumTouchHeight
                onClicked: backend.startCamera()
            }
            WarmButton {
                objectName: "stopCameraButton"
                text: "关闭相机"
                enabled: root.zedRunning
                buttonColor: Theme.danger
                Layout.preferredWidth: 140
                Layout.preferredHeight: Theme.minimumTouchHeight
                onClicked: stopCameraDialog.open()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 180
            radius: Theme.cardRadius
            color: Theme.text
            border.color: Theme.border
            clip: true

            Image {
                id: cameraImage
                objectName: "cameraImage"
                anchors.fill: parent
                anchors.margins: 1
                visible: backend.cameraFrameCounter > 0
                source: backend.cameraFrameCounter > 0 ? "image://camera/frame/" + backend.cameraFrameCounter : ""
                cache: false
                asynchronous: false
                fillMode: Image.PreserveAspectFit
            }

            Label {
                objectName: "cameraPlaceholder"
                anchors.centerIn: parent
                width: parent.width - 48
                visible: backend.cameraFrameCounter === 0
                text: backend.cameraStreamState === "camera_off"
                    ? "相机未开启，点击「开启相机」后等待画面"
                    : "等待画面…"
                color: Theme.surface
                font.pixelSize: 18
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }

            Rectangle {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 12
                visible: backend.cameraFrameCounter > 0 && backend.cameraStreamState !== "ok"
                radius: Theme.cardRadius
                color: Theme.warningSoft
                implicitWidth: staleLabel.implicitWidth + 24
                implicitHeight: staleLabel.implicitHeight + 12
                Label {
                    id: staleLabel
                    anchors.centerIn: parent
                    text: "画面已停止更新，显示的是最后一帧"
                    color: Theme.text
                    font.pixelSize: 14
                }
            }
        }

        Label {
            text: "仅在本页打开时订阅画面，约 5 帧/秒；切到其他页面即停止订阅"
            color: Theme.muted
            font.pixelSize: 14
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
    }

    Dialog {
        id: stopCameraDialog
        objectName: "stopCameraDialog"
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape
        title: "关闭 ZED 相机？"
        width: Math.min(root.width - 64, 560)
        height: 260
        anchors.centerIn: parent
        contentItem: Label {
            text: "巡检、视觉感知等其他任务可能正在使用相机，关闭后这些任务将拿不到画面。\n\n确认关闭相机？"
            color: Theme.text
            font.pixelSize: 16
            wrapMode: Text.Wrap
        }
        footer: Item {
            implicitHeight: 64
            RowLayout {
                anchors.fill: parent
                spacing: 10
                Item { Layout.fillWidth: true }
                WarmButton { objectName: "cancelStopCameraButton"; text: "取消"; Layout.preferredWidth: 120; Layout.preferredHeight: 48; buttonColor: Theme.muted; onClicked: stopCameraDialog.close() }
                WarmButton { objectName: "confirmStopCameraButton"; text: "确认关闭"; buttonColor: Theme.danger; Layout.preferredWidth: 140; Layout.preferredHeight: 48; onClicked: { stopCameraDialog.close(); backend.stopCamera() } }
            }
        }
    }
}
